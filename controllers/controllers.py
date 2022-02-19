import asyncio
from controllers.bonds import frax_bond, rome_frax_bond
from controllers.rebase import rebase
from datetime import datetime
from logger.logger import Logger
from models.rome_interface import RomeInterface
from models.transactions_wrapper import TransactionsWrapper
from web3 import Web3


web3 = Web3(Web3.WebsocketProvider("wss://moonriver.api.onfinality.io/public-ws"))
rome_interface = RomeInterface(web3)
tx_performer = TransactionsWrapper(rome_interface)
logger = Logger()


async def optimize_rebase():
    while True:

        # Gathering pending rewards informations: individual bonds + total balance
        pending_rewards = rome_interface.get_all_bond_pending_rewards()

        await asyncio.sleep(5)

        # Checking number of blocks before next rebase (1 block ~= 5sec)
        next_rebase = rome_interface.check_blocks_before_rebase()
        print(f"{next_rebase} blocks before rebase\n")

        # If ~5min left, claim and autostake pending rewards
        if next_rebase < 30:
            rebase_result = rebase(tx_performer, pending_rewards)
            print("Successfully claimed and autostaked !\n")
            logger.log_move(
                operation="REBASE",
                data=rebase_result
            )

            await asyncio.sleep(300)


async def optimize_bonds():
    while True:

        # Gathering all important informations: discounts, srome balance, and pending rewards
        bond_data = {
            'frax_discount': rome_interface.get_bond_discount(rome_interface.bond_frax_contract),
            'rome_frax_discount': rome_interface.get_bond_discount(rome_interface.bond_rome_frax_lp_contract),
            'srome_balance': rome_interface.get_stacked_balance(),
            'pending_rewards': rome_interface.get_all_bond_pending_rewards()
        }

        print(datetime.now())
        print(
            f'FRAX: {bond_data["frax_discount"]} %\n'
            f'ROME-FRAX LP: {bond_data["rome_frax_discount"]} %\n'
            f'Pending bond rewards: {bond_data["pending_rewards"]["total"]} ROME\n'
        )

        # Checking if we'll use pending rewards.
        # If user has decided to use pending in his setting,
        # And his pending rewards > min sRome balance to bond defined in settings
        # And his pending rewards > his sRome balance, we can use pending rewards.
        if rome_interface.settings["use_pending_rewards"] and \
            bond_data["pending_rewards"]["total"] > rome_interface.settings["min_srome_balance_to_bond"] and \
            bond_data["pending_rewards"]["total"] > bond_data["srome_balance"]:
            use_pending = True
        else:
            use_pending = False

        # Two conditions to meet before bonding: Discount A > Discount B and Discount > min discount defined in settings

        # FRAX BOND
        if bond_data["frax_discount"] > bond_data["rome_frax_discount"] and \
                bond_data["frax_discount"] > rome_interface.settings["min_bond_discount"]:

            # Condition 1 met.
            # Now, we have to check if user has enough balance to bond.
            if bond_data["srome_balance"] + bond_data["pending_rewards"]["frax"] > rome_interface.settings["min_srome_balance_to_bond"] or use_pending:

                print(f"Good discount found on FRAX: {bond_data['frax_discount']} %")

                # We can finally process our bond.
                bond_result = frax_bond(
                    tx_performer,
                    bond_data,
                    use_pending
                )
                print("Frax bond successful !\n")
                logger.log_move(
                    operation="BOND",
                    data=bond_result
                )

            else:
                print(f"Good discount found on FRAX: {bond_data['frax_discount']} %, but not enough sRome balance !")

        # ROME-FRAX BOND
        elif bond_data["rome_frax_discount"] > bond_data["frax_discount"] and \
                bond_data["rome_frax_discount"] > rome_interface.settings["min_bond_discount"]:

            if bond_data["srome_balance"] + bond_data["pending_rewards"]["rome_frax"] > rome_interface.settings["min_srome_balance_to_bond"] or use_pending:

                print(f"Good discount found on ROME-FRAX LP: {bond_data['rome_frax_discount']} %")

                bond_result = rome_frax_bond(
                    tx_performer,
                    bond_data,
                    use_pending
                )
                print("Rome-Frax LP bond successful !\n")
                logger.log_move(
                    operation="BOND",
                    data=bond_result
                )

            else:
                print(f"Good discount found on ROME-FRAX LP: {bond_data['rome_frax_discount']} %, but not enough sRome balance !")

        # Await 2sec then repeat
        await asyncio.sleep(2)


async def main():
    tasks = [asyncio.create_task(coro()) for coro in (optimize_rebase, optimize_bonds)]
    await asyncio.wait(tasks)
