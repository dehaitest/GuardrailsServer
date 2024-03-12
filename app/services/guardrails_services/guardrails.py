import json
from ..LLMs.assistant import Assistant
from ..LLMs.chatgpt import Chatgpt_json
from ..prompt_service import get_prompt_by_name
from ...core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

class Guardrails:
    def __init__(self, client, assistant, thread_id, guardrails_prompts, prompts, chatgpt_json) -> None:
        self.client = client
        self.assistant = assistant
        self.thread_id = thread_id
        self.guardrails_prompts = guardrails_prompts
        self.prompts = prompts
        self.chatgpt_json = chatgpt_json
        self.steps = []
        self.iscontinue = ""

    @classmethod
    async def create(cls, db: AsyncSession, user_settings):
        guardrails_prompts = [
            {"name": 'sensitive_information', "content": await cls.get_prompt_by_name(db, 'sensitive_information'), "order": 5},
            {"name": 'topic', "content": await cls.get_prompt_by_name(db, 'topic'), "order": -5},
            {"name": 'bias', "content": await cls.get_prompt_by_name(db, 'bias'), "order": 2},
            {"name": 'evaluative', "content": await cls.get_prompt_by_name(db, 'evaluative'), "order": 3},
        ]
        prompts = {
            "continue": await cls.get_prompt_by_name(db, 'continue'),
            "instruction": await cls.get_prompt_by_name(db, 'instruction'),
            "output": await cls.get_prompt_by_name(db, 'output')
        }
        assistant_init = await Assistant.create({'openai_key': settings.OPENAI_KEY})
        chatgpt_settings = {'model': settings.OPENAI_MODEL, 'openai_key': settings.OPENAI_KEY}
        chatgpt_json = await Chatgpt_json.create(chatgpt_settings)
        init_instruction = user_settings.get("instruction") or prompts.get("instruction")
        user_settings.update({'instruction': init_instruction, "model": settings.OPENAI_MODEL})
        if user_settings.get("assistant_id"):
            assistant = await assistant_init.load_assistant(user_settings)
            assistant = await assistant_init.update_assistant(user_settings)
        else:
            assistant = await assistant_init.create_assistant(user_settings)
            user_settings.update({'assistant_id': assistant.id})
        if not user_settings.get("thread_id"):
            thread = await assistant_init.create_thread()
            user_settings.update({'thread_id': thread.id})
            thread_id = thread.id

        return cls(assistant_init.client, assistant, thread_id, guardrails_prompts, prompts, chatgpt_json)
    
    @staticmethod
    async def get_prompt_by_name(db: AsyncSession, name: str):
        prompt = await get_prompt_by_name(db, name)
        return prompt.prompt if prompt else ''

    async def run_step(self, step, message_data):
        if step.get("name") == "input":
            await self.client.beta.threads.messages.create(
                thread_id=self.thread_id,
                role="user",
                content=step.get("content"),
                file_ids=json.loads(message_data).get('file_ids', [])
                )
            yield {"type": "chain", "name": step.get("name"), "content": "User input message: " + step.get("content")}
            yield {"type": "system", "name": "message", "content": "Loading file... \n Processing user message... "}
        else:
            yield {"type": "system", "name": "message", "content": "Processing step: " + step.get("name")}
            await self.client.beta.threads.messages.create(
                thread_id=self.thread_id,
                role="user",
                content=step.get("content"),
                )
            run = await self.client.beta.threads.runs.create(
                thread_id=self.thread_id,
                assistant_id=self.assistant.id)

            while run.status == "queued":
                await asyncio.sleep(1)
                run = await self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread_id,
                    run_id=run.id)

            while run.status == "in_progress":
                await asyncio.sleep(1)
                run = await self.client.beta.threads.runs.retrieve(
                    thread_id=self.thread_id,
                    run_id=run.id)
            
            # yield system message
            run_list = await self.client.beta.threads.runs.steps.list(
                thread_id=self.thread_id,
                run_id=run.id)
            for run_step in run_list.data:
                if getattr(run_step.step_details, 'message_creation', None):
                    message = await self.client.beta.threads.messages.retrieve(
                        thread_id=self.thread_id,
                        message_id=run_step.step_details.message_creation.message_id)
                    yield {"type": "system", "name": "message", "content": message.content[0].text.value}
                
            messages = await self.client.beta.threads.messages.list(thread_id=self.thread_id)

            if step.get("name") == "output":
                yield {"type": "chain", "name": step.get("name"), "content": "The final result is:" + messages.data[0].content[0].text.value}
                yield {"type": "system", "name": "message", "content": "End of response"}
            else:
                yield {"type": "chain", "name": step.get("name"), "content": messages.data[0].content[0].text.value}

            # if step.get("order") < 0: 
            #     prompt = [{"role": "system", "content": self.prompts.get('continue')}]
            #     prompt.append({"role": "user", "content": "{}".format(messages.data[0].content[0].text.value)})
            #     yield {"type": "system", "name": "message", "content": "Determine whether the conversation can be continued."}
            #     response = await self.chatgpt_json.process_message(prompt)
            #     result = json.loads(response.choices[0].message.content)
            #     self.iscontinue = result.get("continue")
            #     yield {"type": "system", "name": "message", "content": self.iscontinue}

    async def build_chain(self, message_data):
        user_guardrails = json.loads(message_data).get("guardrails")
        for user_guardrail in user_guardrails:
            if step := next((item for item in self.guardrails_prompts if item["name"] == user_guardrail), None):
                self.steps.append(step)
        self.steps.append({"name": "processing", "content": "Continue processing user input message", "order": 0})
        self.steps.append({"name": "input", "content": json.loads(message_data).get('message'), "order": -100})
        self.steps.append({"name": "output", "content": self.prompts.get('output'), "order": 100})
        self.steps.sort(key=lambda x: x["order"])


    async def guardrails(self, message_data):
        self.steps = []
        self.iscontinue = ""
        yield message_data
        await self.build_chain(message_data)
        yield {"chain": self.steps}
        for step in self.steps:
            # if self.iscontinue == "False":
            #     break
            async for response in self.run_step(step, message_data):
                yield response
        yield "__END_OF_RESPONSE__"

        