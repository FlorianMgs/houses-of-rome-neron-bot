from .rome_contracts import RomeContracts
from .account_interface import Web3Account


class RomeInterface(Web3Account, RomeContracts):
    def __init__(self, web3):
        Web3Account.__init__(self, web3),
        RomeContracts.__init__(self, web3)

    def get_total_rome_balance(self) -> float:
        """
        Get total ROME balance:
        - staked balance is sRome balance
        - in_bonds is pending bonded ROME across all bond contracts
        - locked is balance locked for campaign. We first check for user profile in conscription contract,
        we get his gons and we pass it as argument to balanceForGons() method of sRome contract.
        :return: float representing total ROME balance.
        """
        staked_balance = self.srome_contract.functions.balanceOf(self.account_address).call()
        in_bonds = self.check_deposited_bonds()
        locked = self.srome_contract.functions.balanceForGons(
            self.rome_conscription_contract.functions.profiles(self.account_address).call()[3]
        ).call()
        return self.convert_rome_to_ether(staked_balance + in_bonds['frax'] + in_bonds['rome_frax'] + in_bonds['gohm'] + locked)

    def get_stacked_balance(self) -> float:
        return self.convert_rome_to_ether(self.srome_contract.functions.balanceOf(self.account_address).call())

    def check_deposited_bonds(self) -> dict:
        """
        Check if there is pending rewards in a bond
        :return: dict with bond currency as keys and bool as values
        """
        return {
            'frax': self.bond_frax_contract.functions.bondInfo(self.account_address).call()[0],
            'rome_frax': self.bond_rome_frax_lp_contract.functions.bondInfo(self.account_address).call()[0],
            'gohm': self.bond_gohm_contract.functions.bondInfo(self.account_address).call()[0]
        }

    def get_pending_bond_reward(self, bond_contract) -> float:
        """
        Get pending rewards for a given contract.
        :param bond_contract: bond contract instance
        :return: pending rewards in ether
        """
        return self.convert_rome_to_ether(
            bond_contract.functions.pendingPayoutFor(self.account_address).call()
        )

    def get_all_bond_pending_rewards(self) -> dict:
        """
        Get total pending rewards across all bond contracts.
        :return: Dict containing individual pending rewards and total pending rewards.
        """
        frax_pending_reward = self.get_pending_bond_reward(self.bond_frax_contract)
        rome_frax_pending_reward = self.get_pending_bond_reward(self.bond_rome_frax_lp_contract)
        gohm_pending_reward = self.get_pending_bond_reward(self.bond_gohm_contract)
        return {
            'frax': frax_pending_reward,
            'rome_frax': rome_frax_pending_reward,
            'gohm': gohm_pending_reward,
            'total': frax_pending_reward + rome_frax_pending_reward + gohm_pending_reward
        }

    def convert_rome_to_ether(
            self,
            rome_amount_in_wei: int
    ) -> float:
        """
        Converts ROME amount in wei to a human-readable amount in ether.
        :param rome_amount_in_wei: int representing amount to convert.
        :return: converted amount in ether with the nine ROME decimals.
        """
        return float(self.web3.fromWei(rome_amount_in_wei, 'ether')) / 0.000000001

    def get_rome_market_price(self) -> float:
        """
        :return: Float representing ROME market price in usd
        """
        return self.frax_contract.functions.balanceOf(
            self.rome_frax_lp_address
        ).call() / self.rome_contract.functions.balanceOf(
            self.rome_frax_lp_address
        ).call() * 0.000000001

    def check_blocks_before_rebase(self) -> int:
        """
        :return: integer representing remaining blocks before sROME rebase
        """
        return self.staking_rome_contract.functions.epoch().call()[2] - self.web3.eth.get_block('latest')['number']

    def get_bond_discount(self, bond_contract) -> float:
        """
        :param bond_contract: bond contract to get discount
        :return: float as discount percentage
        """
        rome_market_price = self.get_rome_market_price()
        bond_price = float(self.web3.fromWei(bond_contract.functions.bondPriceInUSD().call(), 'ether'))
        return 100 - (bond_price * 100 / rome_market_price)

    def claim_bond_reward(
            self,
            bond_contract,
            gas: int,
            gasprice: int,
            do_autostake=True
    ) -> dict:
        """
        use redeem() function on the given bond contract to automatically claim bonding reward.
        :param do_autostake: boolean to autostake or not. True by default.
        :param bond_contract: the given bond contract
        :return: dict with tx_receipt, tx_hash and tx_status
        """
        tx_result, amount_staked = {}, 0

        for i in range(0, 3):
            # At 3 tries, if tx still failed, return tx result
            # If tx fails, retry with more gas

            tx = bond_contract.functions.redeem(
                self.account_address,
                do_autostake
            ).buildTransaction(
                self.build_tx_dict(
                    gas,
                    gasprice,
                )
            )
            tx_result = self.sign_and_send_tx(tx)

            if tx_result['tx_status'] == 1:
                amount_hex = ""
                for log in tx_result['tx_receipt']['logs']:
                    amount_hex = log['data']
                amount_staked = self.convert_rome_to_ether(self.web3.toInt(hexstr=amount_hex))

                print(f'Successfully redeemed {amount_staked} ROME.\nTx Hash: {tx_result["tx_hash"]}')
                break

            else:
                amount_staked = 0
                print(f'[FAIL] - Transaction failed: likely not enough gas.\nTx Hash: {tx_result["tx_hash"]}')
                gas += gas * 0.2
                gasprice += 1

        return {
            'tx_type': 'claim_and_autostake',
            'tx_hash': tx_result['tx_hash'],
            'tx_status': tx_result['tx_status'],
            'rome_staked': amount_staked
        }

    def swap_rome_for_frax(
            self,
            gas: int,
            gasprice: int,
            total_balance=True
    ) -> dict:
        """
        Swap web3_interface tokens for frax. if total_balance is set to false (in case of adding web3_interface-frax lp),
        it will swap half web3_interface balance for frax.
        :param total_balance: bool for swapping total balance or not
        :return: dict with tx_hash and tx_status
        """
        tx_result, rome_swapped, frax_received_in_wei = {}, 0, 0
        if total_balance:
            # In case we want to bond FRAX
            rome_to_swap = self.rome_contract.functions.balanceOf(self.account_address).call()
        else:
            # In case we want to bond ROME / FRAX LP
            rome_to_swap = round(self.rome_contract.functions.balanceOf(self.account_address).call() / 2)

        # Approve Solarbeam to spend our ROME tokens before swapping
        approve_tx_result = self.approve_token_spending(
            token_to_spend_contract=self.rome_contract,
            amount=rome_to_swap,
            spender_address=self.solarbeam_router_address,
            gas=gas,
            gasprice=gasprice
        )

        if approve_tx_result['tx_status'] == 1:
            print("Spending Approved")
        else:
            print("Spending not approved")
            return approve_tx_result

        # Assuming spending approve, we can swap ROME for FRAX
        # At 3 tries, if tx still failed, return tx result
        # If tx fails, retry with more gas
        for i in range(0, 3):
            tx = self.solarbeam_router_contract.functions.swapExactTokensForTokens(
                rome_to_swap,
                0,
                [self.rome_address, self.frax_address],
                self.account_address,
                1673825868
            ).buildTransaction(
                self.build_tx_dict(
                    gas,
                    gasprice
                )
            )
            tx_result = self.sign_and_send_tx(tx)

            # get frax received in case of success
            if tx_result['tx_status'] == 1:
                amount_hex = ""
                for i, log in enumerate(tx_result['tx_receipt']['logs']):
                    if i == 2:
                        amount_hex = log['data']
                        break
                frax_received_in_wei = self.web3.toInt(hexstr=amount_hex)
                rome_swapped = self.convert_rome_to_ether(rome_to_swap)
                print(f'Successfully swapped {rome_swapped} ROME for {self.web3.fromWei(frax_received_in_wei, "ether")} FRAX.\nTx Hash: {tx_result["tx_hash"]}')
                break

            else:
                print(f'[FAIL] - Transaction failed: likely not enough gas.\nTx Hash: {tx_result["tx_hash"]}')
                gas += gas * 0.2
                gasprice += 1

        return {
            'tx_type': 'swap',
            'tx_hash': tx_result['tx_hash'],
            'tx_status': tx_result['tx_status'],
            'rome_swapped': rome_swapped,
            'frax_received_wei': frax_received_in_wei
        }

    def add_rome_frax_lp(
            self,
            gas: int,
            gasprice: int,
            frax_to_add_in_wei: int
    ) -> dict:
        """
        Adding ROME/FRAX liquidity through solarbeam router contract.
        :param gas: gas to use for transaction
        :param gasprice_in_gwei: gasprice in gwei
        :return: dict with tx_receipt, tx_hash and tx_status
        """
        tx_result, rome_frax_lp_token_balance = {}, 0

        amount_rome_desired = self.rome_contract.functions.balanceOf(self.account_address).call()
        amount_frax_desired = frax_to_add_in_wei

        # Here we apply 1% slippage to the desired amount
        amount_rome_min = round(amount_rome_desired - amount_rome_desired * 0.01)
        amount_frax_min = round(amount_frax_desired - amount_frax_desired * 0.01)

        # Approving Solarbeam to spend ROME before adding liquidity
        approve_tx_result = self.approve_token_spending(
            token_to_spend_contract=self.rome_contract,
            amount=amount_rome_desired,
            spender_address=self.solarbeam_router_address,
            gas=gas,
            gasprice=gasprice
        )
        if approve_tx_result['tx_status'] == 1:
            print("Spending Approved")
        else:
            print("Spending not approved")
            return approve_tx_result

        # Assuming spending is approved, we can add liquidity
        # At 3 tries, if tx still failed, return tx result
        # If tx fails, retry with more gas
        for i in range(0, 3):
            tx = self.solarbeam_router_contract.functions.addLiquidity(
                self.rome_address,
                self.frax_address,
                amount_rome_desired,
                amount_frax_desired,
                amount_rome_min,
                amount_frax_min,
                self.account_address,
                1673825868
            ).buildTransaction(
                self.build_tx_dict(
                    gas,
                    gasprice
                )
            )
            tx_result = self.sign_and_send_tx(tx)

            rome_frax_lp_token_balance = self.web3.fromWei(
                self.rome_frax_lp_contract.functions.balanceOf(self.account_address).call(), 'ether'
            )

            if tx_result['tx_status'] == 1:
                print(f'Successfully added ROME-FRAX liquidity Token received: {rome_frax_lp_token_balance}.\nTx Hash: {tx_result["tx_hash"]}')
                break
            else:
                print(f'[FAIL] - Transaction failed: likely not enough gas.\nTx Hash: {tx_result["tx_hash"]}')
                gas += gas * 0.2
                gasprice += 1

        return {
            'tx_type': 'add_liquidity',
            'tx_hash': tx_result['tx_hash'],
            'tx_status': tx_result['tx_status'],
            'lp_token_amount': rome_frax_lp_token_balance
        }

    def deposit_bond(
            self,
            gas: int,
            gasprice: int,
            bond_contract,
            bond_contract_address,
            bonded_token_contract,
            frax_bond=False,
            frax_to_bond=0
    ) -> dict:
        """
        Deposit FRAX or ROME-FRAX LP to corresponding bond contract.
        :param frax_bond: Boolean: if true, we want to bond frax but not necessary the entire balance,
        so we give the amount of FRAX in wei to bond
        :param frax_to_bond: if frax bonding, precise the frax amount to bond.
        :param bond_contract: the bond contract instance
        :param bond_contract_address: the bond contract address
        :param bonded_token_contract: the token to bond contract
        :return: dict containing tx result, tx hash and tx status
        """

        tx_result = {}

        # Approving bond_contract to spend token
        if frax_bond:
            amount_to_bond = frax_to_bond
        else:
            amount_to_bond = bonded_token_contract.functions.balanceOf(self.account_address).call()

        approve_tx_result = self.approve_token_spending(
            token_to_spend_contract=bonded_token_contract,
            amount=amount_to_bond,
            spender_address=bond_contract_address,
            gas=gas,
            gasprice=gasprice
        )
        if approve_tx_result['tx_status'] == 1:
            print("Spending Approved")
        else:
            print("Spending not approved")
            return approve_tx_result

        # Assuming spending is approved, we can deposit our tokens to bond contract
        # At 3 tries, if tx still failed, return tx result
        # If tx fails, retry with more gas
        for i in range(0, 3):
            max_price = bond_contract.functions.bondPrice().call()
            tx = bond_contract.functions.deposit(
                amount_to_bond,
                max_price,
                self.account_address
            ).buildTransaction(
                self.build_tx_dict(
                    gas,
                    gasprice
                )
            )
            tx_result = self.sign_and_send_tx(tx)

            if tx_result['tx_status'] == 1:
                print(f'Successfully bonded.\nTx Hash: {tx_result["tx_hash"]}')
                break
            else:
                print(f'[FAIL] - Transaction failed: likely not enough gas.\nTx Hash: {tx_result["tx_hash"]}')
                gas += gas * 0.2
                gasprice += 1

        return {
            'tx_type': 'deposit_bond',
            'tx_hash': tx_result['tx_hash'],
            'tx_status': tx_result['tx_status']
        }

    def unstake(
            self,
            gas: int,
            gasprice: int
    ) -> dict:
        """
        Unstake all staked tokens
        :param gas: gas to use un wei
        :param gasprice_in_gwei: gasprice in gwei
        :return: dict containing tx hash, tx receipt and tx status
        """
        tx_result, unstaked_amount = {}, 0

        amount_to_unstake = self.srome_contract.functions.balanceOf(self.account_address).call()

        for i in range(0, 3):
            tx = self.staking_rome_contract.functions.unstake(
                amount_to_unstake,
                True
            ).buildTransaction(
                self.build_tx_dict(
                    gas,
                    gasprice
                )
            )
            tx_result = self.sign_and_send_tx(tx)

            unstaked_amount = self.convert_rome_to_ether(amount_to_unstake)
            if tx_result['tx_status'] == 1:
                print(f'Successfully unstaked {unstaked_amount} ROME.\nTx Hash: {tx_result["tx_hash"]}')
                break
            else:
                print(f'[FAIL] - Transaction failed: likely not enough gas.\nTx Hash: {tx_result["tx_hash"]}')
                gas += gas * 0.2
                gasprice += 1

        return {
            'tx_type': 'unstake',
            'tx_hash': tx_result['tx_hash'],
            'tx_status': tx_result['tx_status'],
            'unstaked_rome_amount': unstaked_amount
        }
