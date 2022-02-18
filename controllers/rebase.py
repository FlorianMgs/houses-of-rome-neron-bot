

def rebase(
        tx_performer,
        pending_rewards: dict,
) -> dict:

    # Workflow
    frax_tx, rome_frax_tx, gohm_tx = {}, {}, {}
    if pending_rewards['frax'] > tx_performer.rome_interface.settings['min_pending_rewards_to_claim']:
        frax_tx = tx_performer.redeem_frax(do_autostake=True)

    if pending_rewards['rome_frax'] > tx_performer.rome_interface.settings['min_pending_rewards_to_claim']:
        rome_frax_tx = tx_performer.redeem_rome_frax(do_autostake=True)

    if pending_rewards['gohm'] > tx_performer.rome_interface.settings['min_pending_rewards_to_claim']:
        gohm_tx = tx_performer.redeem_gohm(do_autostake=True)

    return {
        'path': [
            frax_tx,
            rome_frax_tx,
            gohm_tx
        ]
    }
