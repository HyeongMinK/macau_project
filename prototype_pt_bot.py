from openai import OpenAI
import os
import time




api_key = os.getenv('OPENAI_API_KEY')  # 환경 변수에서 API 키를 가져옵니다.
client = OpenAI(api_key=api_key)
if not api_key:
    raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")



def delete_messages(id):
# 스레드의 메시지 목록을 불러오기
    messages = client.beta.threads.messages.list(thread_id=id)
    try:
        # 메시지 목록에서 모든 메시지 삭제하기
        for message in messages:
            message_id = message.id
            client.beta.threads.messages.delete(thread_id=id, message_id=message_id)
    except Exception as e:
        print("")

def gpt_call(client, text):
    thread_id = "thread_nJyOZmEHQaabCI1wcOLjzgNs"
    
    thread_message = client.beta.threads.messages.create(thread_id, role="user", content=text)    
    
    content = f"""
Content:
"""

    run = client.beta.threads.runs.create(thread_id=thread_id, assistant_id="asst_QvnqTXw1LoxeqmwHAn2IMVoW", instructions=content, additional_instructions
 = f""  )

    run_id = run.id
    
    timeout = 25
    interval = 1  # 상태 확인 간격을 1초로 증가
    start_time = time.time()

    while time.time() - start_time < timeout:
        time.sleep(interval)

        run_status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        if run_status.status == "completed":
            messages = client.beta.threads.messages.list(thread_id)
            latest_message = max(messages.data, key=lambda x: x.created_at)  # 최신 메시지 찾기
            return latest_message.content[0].text.value if latest_message.content else "No response."

    return "Timeout: No response received within the expected time."