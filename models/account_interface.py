from web3 import Web3
from dotenv import load_dotenv
import json
import os

load_dotenv()
with open('./settings.json') as f:
    SETTINGS = json.load(f)


class Web3Account:
    def __init__(self, web3):
        self.web3 = web3
        self.account_address = self.web3.toChecksumAddress(os.getenv('WALLET_ADDRESS'))
        self.private_key = os.getenv('PRIVATE_KEY')
        self.settings = SETTINGS

    # --------- WEB3 HELPER RELATED METHODS ---------

    def build_tx_dict(
            self,
            gas: int,
            gasprice: int
    ) -> dict:
        """
        :param gas: gas amount to spend for the transaction in wei
        :param gasprice: gas price in gwei
        :return: the dict to give in argument to web3 buildTransaction method with custom gas/gasprice.
        """
        return {
            'nonce': self.web3.eth.get_transaction_count(self.account_address),
            'from': self.account_address,
            'gas': gas,
            'gasPrice': Web3.toWei(gasprice, 'gwei'),
            'chainId': 1285
        }

    def sign_and_send_tx(
            self,
            tx
    ) -> dict:
        """
        Sign and send given transaction.
        :param tx: web3 Transaction object
        :return: dict containing tx receipt and tx status (success, failed or still pending)
        """
        signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
        sent_tx = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_hash = self.web3.toHex(sent_tx)
        tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
        tx_status = tx_receipt['status']
        return {
            'tx_receipt': tx_receipt,
            'tx_hash': tx_hash,
            'tx_status': tx_status
        }

    def approve_token_spending(
            self,
            token_to_spend_contract,
            amount: int,
            spender_address,
            gas: int,
            gasprice: int
    ) -> dict:
        """
        Approve token spending.
        :param token_to_spend_contract: token contract where we call approve() function
        :param gas: gas amount to spend for the transaction in wei
        :param amount: amount to spend
        :param spender_address: the spender, most likely solarbeam in our case
        :return: dict with tx_receipt, tx_hash and tx_status
        """
        for i in range(0, 3):
            approve_tx = token_to_spend_contract.functions.approve(
                spender_address,
                amount
            ).buildTransaction(
                self.build_tx_dict(
                    gas,
                    gasprice,
                ))
            tx_result = self.sign_and_send_tx(approve_tx)
            if tx_result['tx_status'] == 1:
                return tx_result
            else:
                gas += gas * 0.2
                gasprice += 1
                if i == 2:
                    return tx_result
