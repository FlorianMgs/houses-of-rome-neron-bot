# The transaction handler to build strategies with.
# methods names are self-explanatory. They calls rome_interface methods with specific arguments
# regarding the transaction to make.
# All methods returns a dict containing transactions informations.


class TransactionsWrapper:
    def __init__(self, rome_interface):
        self.rome_interface = rome_interface

    # -------- REDEEM ---------

    def redeem_frax(self, do_autostake: bool) -> dict:
        print("Redeem FRAX Bond...")
        frax_claim_tx = self.rome_interface.claim_bond_reward(
            bond_contract=self.rome_interface.bond_frax_contract,
            gas=self.rome_interface.settings['default_gas'],
            gasprice=self.rome_interface.settings['default_gasprice'],
            do_autostake=do_autostake
        )
        return frax_claim_tx

    def redeem_rome_frax(self, do_autostake: bool) -> dict:
        print("Redeem ROME-FRAX Bond...")
        rome_frax_claim_tx = self.rome_interface.claim_bond_reward(
            bond_contract=self.rome_interface.bond_rome_frax_lp_contract,
            gas=self.rome_interface.settings['default_gas'],
            gasprice=self.rome_interface.settings['default_gasprice'],
            do_autostake=do_autostake
        )
        return rome_frax_claim_tx

    def redeem_gohm(self, do_autostake: bool) -> dict:
        print("Redeem GOHM Bond...")
        gohm_claim_tx = self.rome_interface.claim_bond_reward(
            bond_contract=self.rome_interface.bond_gohm_contract,
            gas=self.rome_interface.settings['default_gas'],
            gasprice=self.rome_interface.settings['default_gasprice'],
            do_autostake=do_autostake
        )
        return gohm_claim_tx

    # --------- UNSTAKE ---------

    def unstake(self, srome_balance: float) -> dict:
        print(f"Unstaking {srome_balance}")
        unstake_tx = self.rome_interface.unstake(
            gas=self.rome_interface.settings['default_gas'],
            gasprice=self.rome_interface.settings['default_gasprice']
        )
        return unstake_tx

    # --------- SWAP ---------

    def swap(self, total_balance: bool) -> dict:
        if total_balance:
            print("Swapping all ROME for FRAX...")
        else:
            print("Swapping half ROME for FRAX...")
        swap_tx = self.rome_interface.swap_rome_for_frax(
            gas=self.rome_interface.settings['default_gas'],
            gasprice=self.rome_interface.settings['default_gasprice'],
            total_balance=total_balance
        )
        return swap_tx

    # --------- ADD LIQUIDITY ---------

    def add_liquidity(self, frax_amount: int) -> dict:
        print("Adding ROME-FRAX Liquidity...")
        add_liq_tx = self.rome_interface.add_rome_frax_lp(
            gas=self.rome_interface.settings['default_gas'],
            gasprice=self.rome_interface.settings['default_gasprice'],
            frax_to_add_in_wei=frax_amount
        )
        return add_liq_tx

    # --------- BONDING ---------

    def bond_frax(self, frax_amount: int) -> dict:
        print("Bonding FRAX...")
        bonding_tx = self.rome_interface.deposit_bond(
            gas=self.rome_interface.settings['default_gas'],
            gasprice=self.rome_interface.settings['default_gasprice'],
            bond_contract=self.rome_interface.bond_frax_contract,
            bond_contract_address=self.rome_interface.bond_frax_address,
            bonded_token_contract=self.rome_interface.frax_contract,
            frax_bond=True,
            frax_to_bond=frax_amount
        )
        return bonding_tx

    def bond_rome_frax_lp(self) -> dict:
        print("Bonding ROME-FRAX LP...")
        bonding_tx = self.rome_interface.deposit_bond(
            gas=self.rome_interface.settings['default_gas'],
            gasprice=self.rome_interface.settings['default_gasprice'],
            bond_contract=self.rome_interface.bond_rome_frax_lp_contract,
            bond_contract_address=self.rome_interface.bond_rome_frax_lp_address,
            bonded_token_contract=self.rome_interface.rome_frax_lp_address
        )
        return bonding_tx


