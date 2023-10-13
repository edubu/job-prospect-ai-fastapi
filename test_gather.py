import asyncio
import time


async def func1():
    time.sleep(1)
    return "Func1"


async def func2():
    time.sleep(2)
    return "Func2"


async def func3():
    time.sleep(2.5)
    return "Func3"


async def func4():
    time.sleep(3)
    return "Func4"


async def main():
    results = await asyncio.gather(func1(), func2(), func3(), func4())

    print(results)


if __name__ == "__main__":
    asyncio.run(main())
