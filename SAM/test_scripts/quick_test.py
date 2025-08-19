import asyncio

from deprecated.ollamaherder import build_system_prompt


async def main():
    test = build_system_prompt("username", "usernickname")
    print(test)
    

if __name__ == "__main__":
    asyncio.run(main())