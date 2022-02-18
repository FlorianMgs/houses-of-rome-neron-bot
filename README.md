# houses_of_rome_neron_bot
This tool is intended to be used with [Houses Of Rome](https://romedao.finance/).   
It will optimize your sRome balance by claiming and autostaking automatically your pending bond rewards ~5min before each rebase.   
Also, it will automatically bond for you when a good discount opportunity is detected (5% by default).  
If a transaction fails in the process, Neron Bot will try to perform it with more gas (3 times max).   

With Neron Bot, you'll never miss a great discount opportunity again, and you won't have to do all the tedious steps by hand to take advantage of it.


## Features
### Automatic Rebase
- Claim and Autostake pending rewards for each bonds   
- 30 blocks (~=5min) before each ROME rebase   
### Automatic Bonding
- Available on FRAX bonds and ROME-FRAX LP bonds   
- Will use stacked ROME and / or pending rewards   
- Follows this pattern: claim pending rewards without autostaking, unstake ROME, swap ROME for FRAX, add liquidity (only if rome-frax lp discount) and bond.
### Logger
- Log each operation (bond / rebase) with their transactions in a json file.
## Settings
You can customize Neron Bot's behavior with the settings.json file.   
Here are the setting:   
- default_gas: 750000 by default
- default_gasprice: 2.5 by default
- min_bond_discount: 5 by default. The minimum discount percentage to trigger bonding process.
- min_srome_balance_to_bond: 0.2 by default. If you have less stacked rome than this amount, bonding process will not be triggered.
- min_pending_rewards_to_claim: 0.01 by default. The minimum pending reward amount (in a single bond contract) to trigger claims.
- use_pending_rewards: true by default. If you choose to use pending rewards, Neron will check if your stacked ROME balance + pending ROME rewards is greater than min_srome_balance_to_bond before bonding. If it's the case, it will claim without autostaking your pending rewards to use them for the bond.
## Installation
Install [Python 3](https://www.python.org/), then clone this repo:
```
git clone https://github.com/FlorianMgs/houses_of_rome_neron_bot.git
```
Move to the newly created folder, and fill the .env file with your wallet informations.
Then, you have to create a virtual environment:
```
python -m venv env
```
Activate it.
Windows:
```
env\scripts\activate.bat
```
Linux:
```
source env/bin/activate
```
Install required packages:
```
pip install -r requirements.txt
```
You can finally launch the script:
```
python main.py
```
## Heroku Deployment
You might want the bot to run 24/7 on the cloud. To do this, please signup to [Heroku](https://signup.heroku.com/).
Now you can deploy Neron Bot on Heroku:
```
heroku login
heroku git:remote -a houses_of_rome_neron_bot
git add .
git commit -m "Deployment commit"
git push heroku master 
```
Last step, you need to set our wallet address and private key as config vars:
```
heroku config:set WALLET_ADDRESS=your_wallet_address
heroku config:set PRIVATE_KEY=our_private_key
```
Now you're good to go, enjoy !!

## Donations
If you find this tool useful, feel free to send me a coffee! (any Metamask compatible network)      
0x8b85755F6D3D3B6f984F896b219f99BC561Ed057   
