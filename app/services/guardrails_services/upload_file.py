from ..LLMs.assistant import Assistant
from io import BytesIO
from ...core.config import settings 

class UploadUserFile:
    def __init__(self, assistant) -> None:
        self.client = assistant.client

    @classmethod
    async def create(cls):
        assistant_init = await Assistant.create({'openai_key': settings.OPENAI_KEY})
        return cls(assistant_init)
    
    async def upload_user_file(self, user_file):
        try:
            buffer = BytesIO()
            content = await user_file.read()
            buffer.write(content)
            buffer.seek(0)
            file = await self.client.files.create(
                file=buffer,
                purpose='assistants'
            )
            return {'file_name': user_file.filename, 'file_id': file.id, 'content_type': user_file.content_type}
        except Exception as e:
            print(f"An error occurred when uploading file: {e}")
        finally:
            buffer.close()
