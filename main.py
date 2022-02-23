from controllers.controllers import main
import asyncio


if __name__ == "__main__":
    print(
        "----- HOUSES OF ROME NERON BOT -----\n"
        "Automatic Bonding and Rebases Optimization for Houses Of Rome\n"
        "If you like this tool, feel free to offer me a coffee:\n"
        "0x8b85755F6D3D3B6f984F896b219f99BC561Ed057"
    )
    while True:
        try:
            asyncio.run(main())
        except:
            continue
