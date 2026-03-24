import asyncio
import os
import tempfile
import codecs
from typing import AsyncGenerator, List, Dict, Optional
import abc

class ILLMConnector(abc.ABC):
    @abc.abstractmethod
    async def send_message(
        self, persona_id: int, prompt: str, context: List[Dict], system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        pass

class GeminiCLIConnector(ILLMConnector):
    def __init__(self, cli_path: str = "gemini"):
        self.cli_path = cli_path

    async def send_message(
        self, persona_id: int, prompt: str, context: List[Dict], system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        # Leaner Security Notice
        safety_rule = "Notice: Isolated env. No FS access."
        
        full_prompt = ""
        if system_prompt:
            full_prompt += f"System Instruction: {system_prompt}\n{safety_rule}\n\n"
        else:
            full_prompt += f"{safety_rule}\n\n"
        
        # IMPROVED CONTEXT: Increase history count and char limit for better debate quality
        if context:
            full_prompt += "### CONVERSATION HISTORY ###\n"
            for msg in context: # Use all context messages provided by main.py (last 10)
                sender = "Moderator" if msg['sender_type'] == 'user' else msg.get('persona_name', 'Agent')
                # Increase truncation limit to 2000 chars to keep the full context of long responses
                content = (msg['content'][:2000] + '...') if len(msg['content']) > 2000 else msg['content']
                full_prompt += f"{sender}: {content}\n"
            full_prompt += "### END OF HISTORY ###\n\n"
        
        # CLEARER MODERATOR INSTRUCTION
        if prompt:
            full_prompt += f"Moderator: {prompt}"
        else:
            full_prompt += "Moderator: Please review the conversation history above and provide your response to the points made, especially focusing on the last speaker's message."

        with tempfile.TemporaryDirectory() as tmp_dir:
            process = await asyncio.create_subprocess_exec(
                self.cli_path,
                full_prompt,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=tmp_dir,
                env={**os.environ, "PYTHONUNBUFFERED": "1"}
            )

            decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
            
            try:
                while True:
                    chunk = await process.stdout.read(64)
                    if not chunk:
                        break
                    
                    decoded_text = decoder.decode(chunk, final=False)
                    if decoded_text:
                        yield decoded_text
                
                final_text = decoder.decode(b"", final=True)
                if final_text:
                    yield final_text
            finally:
                if process.returncode is None:
                    process.terminate()
                    await process.wait()

    async def cleanup(self):
        pass

# Global Connector Instance
llm_connector = GeminiCLIConnector()
