import asyncio

async def async_counter():
    for i in range(10):
        await asyncio.sleep(0.5)  # 模拟异步等待
        yield i

async def main():
    async for num in async_counter():
        if num > 6:
            break
        print(num)

asyncio.run(main())
