import asyncio
from chat_factory import ChatFactory

async def test_chat(chat_type: str = None):
    chat = ChatFactory.create_chat(chat_type)
    
    user_input = "tell me something about honey."
    print(f"\n用户: {user_input}\n")
    print("助手: ", end='', flush=True)
    
    try:
        async for response in chat.stream_chat(user_input):
            print(response, end='', flush=True)
        print("\n")
    except KeyboardInterrupt:
        print("\n对话被用户中断")
    finally:
        await chat.client.aclose()

if __name__ == "__main__":
    import sys
    chat_type = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(test_chat(chat_type)) 