import os
from pathlib import Path
import threading
import logging
import time
from dotenv import load_dotenv
import speech_recognition as sr
import subprocess
from langchain_ollama import ChatOllama
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from tools.time import get_time
from tools.codex_tool import codex_cli_task
from tools.shell_task import shell_task

# Load environment and optional mic settings
load_dotenv()
MIC_INDEX = os.getenv("MIC_INDEX")
MIC_NAME_KEYWORD = os.getenv("MIC_NAME_KEYWORD")
DEFAULT_SAMPLE_RATE = int(os.getenv("MIC_SAMPLE_RATE", "48000"))
DEFAULT_CHUNK_SIZE = int(os.getenv("MIC_CHUNK_SIZE", "1024"))
TRIGGER_WORD = "jarvis"
CONVERSATION_TIMEOUT = 30  # seconds of inactivity
tts_process = None

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Define Jarvis home folder and ensure it exists
JARVIS_DIR = Path.home() / ".jarvis"
JARVIS_DIR.mkdir(exist_ok=True)
PID_FILE = JARVIS_DIR / "jarvis"
STATUS_FILE = JARVIS_DIR / "jarvis.status"


def store_jarvis_pid():
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    logging.debug(f"📁 Stored PID {os.getpid()} in {PID_FILE}")


def write_status(status: str):
    with open(STATUS_FILE, 'w') as f:
        f.write(status)


def cancel_tts():
    global tts_process
    if tts_process and tts_process.poll() is None:
        try:
            tts_process.terminate()
            tts_process.wait(timeout=1)
            logging.info("🔇 TTS process canceled by user.")
            write_status("canceled")
        except Exception as e:
            logging.warning(f"Failed to cancel TTS process: {e}")


# Function to select a working microphone
def select_microphone(index=None, name_keyword=None, sample_rate=None, chunk_size=None):
    names = sr.Microphone.list_microphone_names()
    for i, name in enumerate(names):
        logging.info(f"Mic {i}: {name}")
    candidates = []
    if index is not None:
        candidates.append((index, names[index] if index < len(names) else None))
    if name_keyword:
        for i, name in enumerate(names):
            if name_keyword.lower() in name.lower():
                candidates.append((i, name))
    candidates.append((None, None))
    for idx, name in candidates:
        try:
            mic = sr.Microphone(device_index=idx, sample_rate=sample_rate, chunk_size=chunk_size)
            logging.info(f"✅ Using mic: {idx} - {name}")
            return mic
        except Exception as e:
            logging.warning(f"Failed to open mic {idx} ({name}): {e}")
    raise RuntimeError("No valid microphone found")


# Initialize recognizer
recognizer = sr.Recognizer()


# TTS via RHVoice command-line at correct path
def speak_text(text: str):
    global tts_process
    write_status("speaking")

    # Kill previous TTS process if running
    if tts_process and tts_process.poll() is None:
        try:
            tts_process.terminate()
            tts_process.wait(timeout=1)
            logging.info("🔇 Previous TTS process terminated.")
        except Exception as e:
            logging.warning(f"Failed to terminate previous TTS process: {e}")

    try:
        tts_process = subprocess.Popen(
            ["/snap/bin/rhvoice.test", "-p", "slt"],
            stdin=subprocess.PIPE
        )

        # Feed input slowly and monitor status
        tts_process.stdin.write(text.encode('utf-8'))
        tts_process.stdin.close()

        # Poll for status while TTS is running
        while tts_process.poll() is None:
            current_status = STATUS_FILE.read_text().strip()
            if current_status == "canceled":
                tts_process.terminate()
                logging.info("❌ TTS canceled mid-speech by user.")
                break
            time.sleep(0.25)

    except FileNotFoundError:
        logging.error("RHVoice not found. Is it installed?")
    except Exception as e:
        logging.error(f"TTS error: {e}")
    finally:
        write_status("listening")

# Initialize LLM + tools
llm = ChatOllama(model="qwen3:1.7b", reasoning=False)
tools = [get_time, codex_cli_task, shell_task]
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are Jarvis, a helpful AI assistant.\n"
     "Use `shell_task` for raw Linux commands (ls, cat, pwd).\n"
     "Use `codex_cli_task` when the user asks you to generate code or automate project scaffolding."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])
agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


# Main function with auto-retry on mic errors
def write():
    mic = None
    try:
        mic = select_microphone(
            index=int(MIC_INDEX) if MIC_INDEX is not None else None,
            name_keyword=MIC_NAME_KEYWORD,
            sample_rate=DEFAULT_SAMPLE_RATE,
            chunk_size=DEFAULT_CHUNK_SIZE
        )
    except Exception as e:
        logging.critical(f"🚨 Initial mic setup failed: {e}")
        return

    conversation_mode = False
    last_interaction_time = None

    while True:
        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=1)
                recognizer.pause_threshold = 0.8
                recognizer.non_speaking_duration = 0.5
                recognizer.dynamic_energy_threshold = True
                logging.info("🎤 Mic active. Say 'Jarvis' to begin.")

                while True:
                    try:
                        if not conversation_mode:
                            write_status("idle")
                            logging.info("🕵️ Listening for wake word...")
                            audio = recognizer.listen(source, timeout=10)
                            transcript = recognizer.recognize_google(audio)
                            logging.info(f"🗣 Heard: {transcript}")

                            if TRIGGER_WORD.lower() in transcript.lower():
                                logging.info("✔ Wake word detected.")
                                speak_text("Yes sir?")
                                conversation_mode = True
                                last_interaction_time = time.time()
                                write_status("listening")
                        else:
                            write_status("listening")
                            logging.info("🎤 Listening for command...")
                            audio = recognizer.listen(source, timeout=10)
                            command = recognizer.recognize_google(audio)
                            logging.info(f"📥 Command: {command}")

                            response = executor.invoke({"input": command})
                            content = response.get("output", "")
                            logging.info(f"✎  Response: {content}")
                            speak_text(content)

                            last_interaction_time = time.time()
                            if time.time() - last_interaction_time > CONVERSATION_TIMEOUT:
                                logging.info("⌛ Timeout. Returning to wake word mode.")
                                conversation_mode = False

                    except sr.WaitTimeoutError:
                        logging.warning("⏱️ No audio input (timeout).")
                        if conversation_mode and time.time() - last_interaction_time > CONVERSATION_TIMEOUT:
                            logging.info("⌛ Conversation timeout. Returning to wake word mode.")
                            conversation_mode = False
                    except sr.UnknownValueError:
                        logging.warning("🤷 Could not understand audio.")
                    except Exception as e:
                        logging.error(f"❌ Error in conversation loop: {e}")
                        raise
        except Exception as e:
            logging.critical(f"🚨 Mic or setup error, retrying: {e}")
            time.sleep(5)
            try:
                mic = select_microphone(
                    index=int(MIC_INDEX) if MIC_INDEX is not None else None,
                    name_keyword=MIC_NAME_KEYWORD,
                    sample_rate=DEFAULT_SAMPLE_RATE,
                    chunk_size=DEFAULT_CHUNK_SIZE
                )
            except Exception as err:
                logging.critical(f"🚨 Mic re-setup failed: {err}")
                time.sleep(5)
                continue


if __name__ == "__main__":
    store_jarvis_pid()
    write()
