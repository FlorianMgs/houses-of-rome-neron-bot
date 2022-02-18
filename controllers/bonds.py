

def frax_bond(
        tx_performer,
        bond_data: dict,
        use_pending: bool
) -> dict:

    settings = tx_performer.rome_interface.settings
    logged_txs = []

    if use_pending:
        print("Using pending rewards...")
        if bond_data["pending_rewards"]["rome_frax"] > settings["min_pending_rewards_to_claim"]:
            tx = tx_performer.redeem_rome_frax(do_autostake=False)
            logged_txs.append(tx)

        if bond_data["pending_rewards"]["gohm"] > settings["min_pending_rewards_to_claim"]:
            tx = tx_performer.redeem_gohm(do_autostake=False)
            logged_txs.append(tx)

        if bond_data["pending_rewards"]["frax"] > settings["min_pending_rewards_to_claim"]:
            tx = tx_performer.redeem_frax(do_autostake=False)
            logged_txs.append(tx)

    else:
        print("Using stacked ROME...")
        if bond_data["pending_rewards"]["frax"] > settings["min_pending_rewards_to_claim"]:
            tx = tx_performer.redeem_frax(do_autostake=False)
            logged_txs.append(tx)

        # After claiming FRAX reawards, we can unstake our total sRome balance
        tx = tx_performer.unstake(bond_data["srome_balance"])
        logged_txs.append(tx)

    # Then, we can swap our ROME for FRAX
    swap_tx = tx_performer.swap(total_balance=True)

    # Finally, we bond our FRAX
    bonding_tx = tx_performer.bond_frax(frax_amount=swap_tx["frax_received_wei"])

    logged_txs = logged_txs + [swap_tx, bonding_tx]
    return {
        'bond': 'FRAX',
        'discount': bond_data['frax_discount'],
        'path': logged_txs
    }


def rome_frax_bond(
        tx_performer,
        bond_data: dict,
        use_pending: bool
) -> dict:

    settings = tx_performer.rome_interface.settings
    logged_txs = []

    if use_pending:
        print("Using pending rewards...")
        if bond_data["pending_rewards"]["frax"] > settings["min_pending_rewards_to_claim"]:
            tx = tx_performer.redeem_frax(do_autostake=False)
            logged_txs.append(tx)

        if bond_data["pending_rewards"]["gohm"] > settings["min_pending_rewards_to_claim"]:
            tx = tx_performer.redeem_gohm(do_autostake=False)
            logged_txs.append(tx)

        if bond_data["pending_rewards"]["rome_frax"] > settings["min_pending_rewards_to_claim"]:
            tx = tx_performer.redeem_rome_frax(do_autostake=False)
            logged_txs.append(tx)

    else:
        print("Using stacked ROME...")
        if bond_data["pending_rewards"]["rome_frax"] > settings["min_pending_rewards_to_claim"]:
            tx = tx_performer.redeem_rome_frax(do_autostake=False)
            logged_txs.append(tx)

        # After claiming ROME-FRAX reawards, we can unstake our total sRome balance
        tx = tx_performer.unstake(bond_data["srome_balance"])
        logged_txs.append(tx)

    # Then, we can swap our ROME for FRAX
    swap_tx = tx_performer.swap(total_balance=False)

    # Now we add rome-frax liquidity
    add_liq_tx = tx_performer.add_liquidity(frax_amount=swap_tx["frax_received_wei"])

    # Finally we can bond
    bonding_tx = tx_performer.bond_rome_frax_lp()

    logged_txs = logged_txs + [swap_tx, add_liq_tx, bonding_tx]
    return {
        'bond': 'ROME-FRAX LP',
        'discount': bond_data['rome_frax_discount'],
        'path': logged_txs
    }
