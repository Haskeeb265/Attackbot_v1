# AttackBot End-to-End Findings Report

- Generated at: `2026-03-25T03:33:39.242817+00:00`
- Report file: `E2E_Runs/E2E_SYSTEM_FINDINGS#6.md`
- Project root: `C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1`
- Test outcome: `completed`

## Requested Mode
- Full end-to-end execution attempted against current M3 stack.
- All feature flags were set to `true` in scan start payload.
- Live-mode policy: no seeded/dummy fallback for primary scan.
- Program selection override active via `E2E_PINNED_PROGRAM_HANDLE` / `E2E_PINNED_PROGRAM_ID`.

## Execution Steps
1. 2026-03-25T03:31:21.738318+00:00 | Starting end-to-end system trace test
1. 2026-03-25T03:31:21.738570+00:00 | .env present (loaded 0 missing keys into process env)
1. 2026-03-25T03:31:22.245389+00:00 | Bringing up stack with docker compose up -d
1. 2026-03-25T03:31:26.218037+00:00 | Health probe scraper: status_code=200
1. 2026-03-25T03:31:26.667082+00:00 | Health probe core-engine: status_code=200
1. 2026-03-25T03:31:59.889059+00:00 | Health probe reporter: status_code=None
1. 2026-03-25T03:32:33.204938+00:00 | Health probe attack-graph-engine: status_code=None
1. 2026-03-25T03:32:33.711738+00:00 | Health probe api-gateway: status_code=200
1. 2026-03-25T03:32:34.482074+00:00 | Connected to database backend=docker-exec (core-engine) | PostgreSQL 16.13 (Debian 16.13-1.pgdg13+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
1. 2026-03-25T03:32:34.482095+00:00 | Pinned program selector configured: E2E_PINNED_PROGRAM_ID=None, E2E_PINNED_PROGRAM_HANDLE='weblate'
1. 2026-03-25T03:32:34.482098+00:00 | HackerOne credentials detected; triggering live scraper sync
1. 2026-03-25T03:32:34.869660+00:00 | Scraper trigger responded with status_code=200
1. 2026-03-25T03:32:35.547510+00:00 | Selected existing real program with scope: 2715b22b-3506-4fb1-bece-95cad2eec341 (weblate) via policy=pinned_program_handle
1. 2026-03-25T03:32:36.679934+00:00 | Queue purge pre-check scan.jobs: ready=0 unacked=0 consumers=1
1. 2026-03-25T03:32:38.054631+00:00 | Queue purge attempt #1 scan.jobs: ok=True status=204 ready_before=0 ready_after=0
1. 2026-03-25T03:32:38.518621+00:00 | Queue purge settle window scan.jobs: settled_unacked=True ready=0 unacked=0
1. 2026-03-25T03:32:39.898872+00:00 | Queue purge attempt #2 scan.jobs: ok=True status=204 ready_before=0 ready_after=0
1. 2026-03-25T03:32:39.898897+00:00 | Waiting for queue baseline before triggering scan: queue=scan.jobs ready=0 unacked=0 timeout=60s
1. 2026-03-25T03:32:40.316965+00:00 | Queue baseline poll scan.jobs: ready=0 unacked=0 consumers=1
1. 2026-03-25T03:32:40.316990+00:00 | Queue baseline reached: scan.jobs ready=0 unacked=0
1. 2026-03-25T03:32:40.316993+00:00 | Triggering core scan with all feature flags enabled
1. 2026-03-25T03:32:51.703288+00:00 | Scan start response included scan_id=ccc0a3c6-a203-4333-a6dc-b54608d8393e
1. 2026-03-25T03:32:52.399050+00:00 | Scan status transition observed: running
1. 2026-03-25T03:33:32.921804+00:00 | Scan status transition observed: partial
1. 2026-03-25T03:33:32.921826+00:00 | Terminal scan status reached: partial

## Runtime Context
- DB connection backend: `docker-exec (core-engine) | PostgreSQL 16.13 (Debian 16.13-1.pgdg13+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit`
- Live HackerOne mode: `False`
- Program source: `existing_real_pinned`
- Program selection policy: `pinned_program_handle`
- Pinned program handle override: `weblate`
- Pinned program ID override: `None`
- Program ID: `2715b22b-3506-4fb1-bece-95cad2eec341`
- Program handle: `weblate`
- Scan ID: `ccc0a3c6-a203-4333-a6dc-b54608d8393e`
- Reconciler pause requested (`E2E_PAUSE_RECONCILER`): `True`
- Queue baseline enforcement (`E2E_ENFORCE_QUEUE_BASELINE`): `True`
- Queue pre-purge enabled (`E2E_QUEUE_PURGE_BEFORE_BASELINE`): `True`
- HackerOne username present in process env: `True`
- HackerOne token present in process env: `True`

### Enabled Feature Flags
```json
{
  "ai_hypothesis": true,
  "api_fuzzing": true,
  "asset_discovery": true,
  "browser_session": true,
  "cors": true,
  "crlf": true,
  "enumeration": true,
  "fingerprinting": true,
  "idor_verification": true,
  "nuclei": true,
  "scenario_runner": true,
  "secret_js": true,
  "secret_repo": true,
  "sqli": true,
  "ssrf": true,
  "takeover": true,
  "xss": true
}
```

## HackerOne Scrape Trigger
```json
{
  "payload": {
    "platform": "hackerone",
    "reason": "lock_held",
    "status": "skipped"
  },
  "status_code": 200
}
```

## Program Selection Audit
| program_id | handle | name | platform | is_active | valid_in_scope_count | selected | reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 52d72dcf-cb60-4d5b-84fd-be662db2c966 | superhuman | Superhuman (formerly Grammarly) | hackerone | True | 24 | False | not selected: run pinned to explicit program selector(s) |
| af01906f-0bf5-4836-91ed-12ed51434d93 | hyperledger | Linux Foundation Decentralized Trust | hackerone | True | 26 | False | not selected: run pinned to explicit program selector(s) |
| 7fbad3cb-02b1-4000-bef4-d066040f9017 | upserve | Upserve  | hackerone | True | 18 | False | not selected: run pinned to explicit program selector(s) |
| 2578e56e-f426-428c-a50b-573e1adf8c2c | malwarebytes | Malwarebytes | hackerone | True | 36 | False | not selected: run pinned to explicit program selector(s) |
| 70e2da39-c246-407f-a60d-050f6ae3e38a | delight_im | delight.im | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| 6509bd60-1659-432e-be5e-66c5e5b5fcc0 | wakatime | WakaTime | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 82d5613c-c6cd-4cc8-9efd-31cae0cafa9f | yoti | Yoti | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| 11806c2d-2ff2-4179-953c-e4e08653ef75 | infogram | Infogram | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| ac00be94-53e5-4095-83db-7535cd0915ea | bumble | Bumble | hackerone | True | 50 | False | not selected: run pinned to explicit program selector(s) |
| 66ec6da6-49b9-4e21-8055-a61fba102feb | wink_jq3al | WINK | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 282a5447-56ca-4f85-8303-a8839c2bd342 | omise | Omise | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| 847c022b-eedb-4514-8487-577af5896c94 | bitwarden | Bitwarden | hackerone | True | 18 | False | not selected: run pinned to explicit program selector(s) |
| f8aae6d2-d7c6-4bdf-8159-a6fdfc30c654 | parrot_sec | Parrot Sec | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 4fa088f1-d644-4e0a-b293-d37ccba494f1 | stellar | Stellar.org | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 7b5b72d1-e72d-4dd8-9237-491ee610ef23 | teradici | Teradici | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| edd64fa2-72fe-437f-9372-770e4ee1d5e8 | autodesk | Autodesk | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| f62490cd-5196-40ec-bb0a-f3b2fcf22c79 | rocket_chat | Rocket.Chat | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 9ff4160d-eedc-4b20-a7d6-e010d1004243 | roblox | Roblox | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| 2715b22b-3506-4fb1-bece-95cad2eec341 | weblate | Weblate | hackerone | True | 6 | True | selected: matched E2E_PINNED_PROGRAM_HANDLE=weblate |
| 93b10688-7d1b-4320-b8ee-bfe72117d9e9 | homebrew | Homebrew | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| df789f05-ba39-4505-bf61-7828ab63ca8b | oportun_vdp | Oportun | hackerone | True | 44 | False | not selected: run pinned to explicit program selector(s) |
| 47b1d47c-e255-4e84-8aee-8a11f8b6b04d | rbkmoney | RBKmoney | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 83dba83c-7800-46fb-8803-93e836527861 | nordsecurity | Nord Security | hackerone | True | 17 | False | not selected: run pinned to explicit program selector(s) |
| a794297f-bcb8-4d68-acb7-d839438ba9a9 | discourse | Discourse | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| d2bab8bd-e481-4066-9910-3de1e9504a91 | nutanix | Nutanix | hackerone | True | 17 | False | not selected: run pinned to explicit program selector(s) |
| 7f006c6f-f484-4671-b7e0-d69326d93335 | mapsmarker_com_e_u | MapsMarker.com e.U. | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 0a82b80b-ab8e-4a41-9a60-6b7a9be82da7 | nintendo | Nintendo | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| 3b6a1bf0-1686-4e6c-88eb-804503540272 | sony | Sony | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| a47ce257-6f5e-48a1-b772-35a9df9031e3 | alvosec | Alvosec | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 12242d30-5139-476d-9d14-a217708f1445 | enjin | Enjin | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| cf594ce9-247b-4f44-8156-e5929d4ed499 | lyst | Lyst | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| cb445c02-3d4b-478f-8e68-a609a4f14581 | disclosure-assistance | Disclosure Assistance | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 4fc994f0-06c5-4f05-967b-3c2931acb801 | xiaomi | Xiaomi | hackerone | True | 28 | False | not selected: run pinned to explicit program selector(s) |
| bc7e9678-0c92-4334-86ec-07e8806eabdf | deptofdefense | U.S. Dept Of Defense | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 900fb79e-04ae-45b7-ab33-cd838129d61b | semrush | Semrush | hackerone | True | 13 | False | not selected: run pinned to explicit program selector(s) |
| 57fe104b-a269-4ad2-938b-7c354af561f0 | brave | Brave Software | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 57f39ae7-c3f7-4a87-855a-1cbd6b31804d | shopify-scripts | shopify-scripts | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 96816aaa-5349-4aba-963d-71618729f38b | cornershop | Cornershop | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| b35f32f3-9609-4a42-a649-01615da02085 | plaid | Plaid | hackerone | True | 13 | False | not selected: run pinned to explicit program selector(s) |
| 280b9aad-1cea-4351-8e02-a0d79a4998c9 | portswigger | PortSwigger Web Security | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| a40a5a61-8166-4d62-b876-5c07694cd275 | toyota | Toyota | hackerone | True | 28 | False | not selected: run pinned to explicit program selector(s) |
| 90bde9b8-c989-4632-bf5a-d293b6b796bd | localizejs | Localize | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 5ea0ad2c-cde6-43e6-abfb-a9cc1b26a159 | hiro | Hiro | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 035805b3-afe7-4a31-9f34-489bc6a8fd79 | gocd | GoCD | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| fd5fce19-154a-4ac5-b5f5-57195a303c01 | acronis | Acronis | hackerone | True | 21 | False | not selected: run pinned to explicit program selector(s) |
| 887314cc-7ee3-411a-a331-c9350a32e1a9 | secnews | SecNews | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 2a311ae4-a7e7-4802-8f34-a9f3460e92f6 | line | LY Corporation | hackerone | True | 20 | False | not selected: run pinned to explicit program selector(s) |
| 8803e1e9-cb0d-47cc-9285-c2d68b0783b1 | pyca | Python Cryptographic Authority | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| d8ab4b8b-93b2-4004-beb8-8bbfa1e21b1a | nextcloud | Nextcloud | hackerone | True | 95 | False | not selected: run pinned to explicit program selector(s) |
| 9f036669-0858-4e4e-9d23-4ab13118ceac | files | Files.com | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| eaa0189f-9acf-4d7e-a70d-2a0ed77ca36e | pushwoosh | Pushwoosh | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| c684f453-1f82-45e6-b844-93c28d299971 | exness | EXNESS | hackerone | True | 18 | False | not selected: run pinned to explicit program selector(s) |
| d55d3055-544c-4136-adf0-d15fc15f6237 | fantasytote | FantasyTote | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 090a5f07-ce11-4469-9e73-24010f3a80a3 | owox | OWOX, Inc. | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 54d5c11e-19b8-4a66-aa8c-1140ecd23c1f | drugs_com | Drugs.com | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| f6651d3e-26c2-49c1-90f0-9bd944c3893e | helium | Helium | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| f79b10f2-3df7-4c9f-898e-5840086eca37 | websummit | WebSummit | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 761ac80f-66e2-4fd6-9481-70e484cc0877 | duckduckgo | DuckDuckGo | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 3c148cff-a608-4f56-8a77-987c58037a9c | aspen | Aspen | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 5d2a438e-4e29-4114-8e36-ed9dc32e2083 | dyson | Dyson | hackerone | True | 66 | False | not selected: run pinned to explicit program selector(s) |
| d4a95676-0077-4014-91df-3c19348b4a12 | phpbb | phpBB | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 6574a210-4243-47f1-903a-17e62c1aa76d | mainwp | MainWP | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| a9064448-4d68-41b1-9cf1-05f5e8621d2e | mariadb | MariaDB | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| ab8e1a2c-a0ad-4769-a264-9ba517a4691d | bitaccess | bitaccess | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| d53dc8a4-bf68-45ce-ab53-4a120ae7bef6 | kiwicom | Kiwi.com | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| 37ae2e7f-43a5-4eed-a751-71138630847a | paragonie | Paragon Initiative Enterprises | hackerone | True | 12 | False | not selected: run pinned to explicit program selector(s) |
| 761e5750-5217-4f08-920f-d29936a63319 | rubygems | RubyGems | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| db9b007c-03ce-40ad-908e-3ea812e5968c | flipkart | Flipkart | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| 55badfee-514b-45b7-b99e-4997ac2bc865 | hyatt | Hyatt Hotels | hackerone | True | 65 | False | not selected: run pinned to explicit program selector(s) |
| 9d62abaa-0175-4570-8e88-a271dfabebcd | monero | Monero | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 5d87b974-96f0-417a-b6e9-0d14de8f31d1 | ruby | Ruby | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 76933b03-e6de-4e97-9565-2893fc617d1d | gm | General Motors | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 46dc2960-85dd-472a-93b1-960dce9744da | bime | Bime | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 09904753-c223-4e62-b17e-0d6dc38b8ef2 | fetlife | FetLife | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| c143311b-955c-4423-99a1-7290cdba3e4d | msd | Merck & Co., Inc., Rahway, NJ, USA | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| b40c11a1-c295-4255-85b5-0ce60a9dee87 | goldmansachs | Goldman Sachs | hackerone | True | 46 | False | not selected: run pinned to explicit program selector(s) |
| 3f3cdf1d-f4e1-45fa-bcba-47f4d81fc3eb | bestbuy | Best Buy | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| f63f2a90-f0e3-4cdf-96eb-40bac07e5df9 | equifax | Equifax-vdp | hackerone | True | 282 | False | not selected: run pinned to explicit program selector(s) |
| 0f488d5a-9479-4ed1-8b55-f0e72df3fdcf | codeigniter | CodeIgniter | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| a7e5f042-3308-45c5-b4fc-071185bb5172 | quora | Quora | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 9e623444-40a2-4e57-a4f9-d2602dd0dfe9 | homebargains | Home Bargains | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| d5053385-c672-4e2b-8db4-e018fefed7b9 | versioncake | Version Cake | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 2f2ce21a-233b-40b1-8c31-492298c369a1 | owncloud | ownCloud | hackerone | True | 15 | False | not selected: run pinned to explicit program selector(s) |
| 46287061-9b5b-4aa7-a6ba-db94e9ed0cec | kiwi-ki | KIWI.KI GmbH | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| f2042332-a4d6-45b7-a3fb-7bc561b7381b | wealthsimple | Wealthsimple | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| e0a1f470-7aaa-4414-8462-42c8af26f1b3 | eternal | Eternal | hackerone | True | 34 | False | not selected: run pinned to explicit program selector(s) |
| 22a8a2e7-061b-4a29-a0de-5a7af172ea84 | deriv | Deriv.com | hackerone | True | 18 | False | not selected: run pinned to explicit program selector(s) |
| d66b31e7-c799-40d1-ab2f-e1067b7253bf | unikrn | Unikrn | hackerone | True | 25 | False | not selected: run pinned to explicit program selector(s) |
| 8de7f146-5819-4672-890a-59554bf2e0e9 | revive_adserver | Revive Adserver | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| cac04df6-0a3a-40d8-bbde-348a61409fbc | clear | CLEAR | hackerone | True | 17 | False | not selected: run pinned to explicit program selector(s) |
| b0863f28-54f0-42bb-b370-fa3598cd4db5 | libsass | LibSass | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 495ea853-bed1-4838-8c6c-2e2a343ce369 | rockstargames | Rockstar Games | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| 0c8722b5-ede6-4ffa-8c7b-aaa604816d97 | ibm | IBM | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 7a279ff5-a537-43f5-8dbb-e25716cce599 | spotify | Spotify | hackerone | True | 43 | False | not selected: run pinned to explicit program selector(s) |
| 7083c062-1ec1-4599-aec0-b224f6dc0708 | starbucks | Starbucks | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| f51c1ce8-5465-4e08-9513-a86c40ae211e | trellix | Trellix | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| 1907a9d6-bdf4-42c1-b9d3-5d2305d0f016 | badoo | Badoo | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 28d644ee-7a67-4069-8762-31069ab71829 | matomo | Matomo | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| 3a7d7cdd-1b47-465e-ac3b-45fd90db7856 | paypal | PayPal | hackerone | True | 41 | False | not selected: run pinned to explicit program selector(s) |
| 2a87c8da-effb-40c8-b1ef-4e84d81f109a | github | GitHub | hackerone | True | 27 | False | not selected: run pinned to explicit program selector(s) |
| 945a71d6-c7be-46a0-870f-a32b5e47f059 | torproject | Tor | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 79c83ee8-2cd5-43b4-b0e2-f3e934d7f715 | nokogiri | Nokogiri | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| b0e179da-8040-494d-9567-b258234c3725 | goodrx | GoodRx | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 0d0d5114-9969-4393-9071-bf154d1e16d1 | grab | Grab | hackerone | True | 33 | False | not selected: run pinned to explicit program selector(s) |
| eb9ab085-6039-4e96-aaf6-4dac6ea347ed | legalrobot | Legal Robot | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| dd946e1b-5c49-4714-83ee-45575f10e4f3 | udemy | Udemy | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 1683e48d-05eb-47c1-bfdc-735e6c83e905 | coursera | Coursera | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| baf35361-d775-4a2e-b4d2-fad7d3c4b5e7 | ips | Invision Power Services, Inc. | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 3d3eea2a-b239-49dd-82ba-f546680a3078 | shopify | Shopify | hackerone | True | 20 | False | not selected: run pinned to explicit program selector(s) |
| 8279e94c-0b6c-451e-b7d2-d34cda6f2604 | mapbox | Mapbox | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| 146a4d3d-b0b1-4706-a367-03837362a672 | moneybird | Moneybird | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| bd52fc34-aeaf-4fde-a97a-ec744cb1faba | kayak | KAYAK | hackerone | True | 12 | False | not selected: run pinned to explicit program selector(s) |
| 28998968-0604-447d-9056-d416260c6e63 | airbnb | Airbnb | hackerone | True | 27 | False | not selected: run pinned to explicit program selector(s) |
| 328b391e-d89f-4511-9db5-22771f0d21f2 | bookingcom | Booking.com | hackerone | True | 49 | False | not selected: run pinned to explicit program selector(s) |
| 5eeacd47-82c6-45a5-a9b6-77a985067d31 | airtable | Airtable | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| e7e52233-b556-4db0-8f5d-9f4fb0f202f2 | ui | Ubiquiti Inc. | hackerone | True | 50 | False | not selected: run pinned to explicit program selector(s) |
| 766b3d4b-e81f-41ed-b4e1-83a83577cce9 | imgur | Imgur | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| d6381f07-6024-4bf2-8c32-d3f4591e677d | mobilevikings | Mobile Vikings | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 59d036ce-4df7-4c1a-a9d7-e3f204d1cc3b | scopely | Scopely | hackerone | True | 26 | False | not selected: run pinned to explicit program selector(s) |
| a667b286-b2d1-49d8-8f77-3645ac3f6ec5 | yelp | Yelp | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| 2117295d-cb19-4e13-af4e-dfa5c4dc69b6 | snapchat | Snapchat | hackerone | True | 40 | False | not selected: run pinned to explicit program selector(s) |
| 2baac140-465e-47ce-b480-e264517dd49f | informatica | Informatica | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 1dbfb46f-0060-43a3-bbcf-835fa46ddd67 | algolia | Algolia | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 94ed7ca6-b7c5-4d41-b2fe-a971cda025bf | glasswire | GlassWire | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 1b54a425-6b50-4c29-a430-ce8258086347 | wordpoints | WordPoints | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| a8637f68-273f-4629-b867-e6bf1e6f8d1c | adobe | Adobe | hackerone | True | 69 | False | not selected: run pinned to explicit program selector(s) |
| 9f4d3604-5979-4f2e-b06e-d77013d9737d | uber | Uber | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 772d0b3f-aaf5-4a63-ac7e-439366b499b7 | greenhouse | Greenhouse.io | hackerone | True | 12 | False | not selected: run pinned to explicit program selector(s) |
| a4dc105d-b8a4-476e-b185-605f86056616 | cert | CERT/CC | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| b7049229-9686-4990-a6b9-10b07d2ef0dd | wp-api | WP API | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 5e0a7d53-dccf-490a-a404-f010fc91ec17 | digitalsellz | DigitalSellz | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 97381019-2390-47ba-b5c2-5719ecbeb1f2 | expressionengine | ExpressionEngine | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 70a23677-501b-49ad-8973-53adc554307e | gitlab | GitLab | hackerone | True | 20 | False | not selected: run pinned to explicit program selector(s) |
| 4762a4ab-3e3e-4ae3-af31-0f44f8ad2c05 | formassembly | FormAssembly | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| 734881ac-1444-4aaf-955b-219f1e8f60eb | urbandictionary | Urban Dictionary | hackerone | True | 16 | False | not selected: run pinned to explicit program selector(s) |
| 4d7dc2a1-d8a4-4b76-be02-508518751a7a | glassdoor | Glassdoor | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| 5e218150-4e91-4bd4-a0c8-051a8445dd60 | stopthehacker | StopTheHacker | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 449b1805-1544-4a0d-8344-5f465ae591a1 | iandunn-projects | Ian Dunn | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 8ea676f5-8147-4474-a1c4-6e305672bbb8 | irccloud | IRCCloud | hackerone | True | 12 | False | not selected: run pinned to explicit program selector(s) |
| b7896e56-914b-48e1-b3d9-b4ca63dd95bd | khanacademy | Khan Academy | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| bdeffc4f-3420-4ba7-a59b-1c2fcdd2f1df | att | AT&T | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| d827dc8a-55f6-4978-b455-02052cb05940 | automattic | Automattic | hackerone | True | 29 | False | not selected: run pinned to explicit program selector(s) |
| d1493d3a-5cbb-455b-916a-d5dd0099bc23 | coinbase | Coinbase | hackerone | True | 28 | False | not selected: run pinned to explicit program selector(s) |
| ee0e4c9a-be48-4224-85c1-883094afc97f | publitas | Publitas | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| a5f0b451-5a93-45d5-ac7c-cfeaae141a67 | tinder | Tinder | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| 0e7e60ef-f025-462f-bfc2-a910a542aa80 | slack | Slack | hackerone | True | 19 | False | not selected: run pinned to explicit program selector(s) |
| b1cd5fc1-82c0-46b2-b7e0-720d9d186264 | basecamp | Basecamp | hackerone | True | 16 | False | not selected: run pinned to explicit program selector(s) |
| 758e92e5-cf77-4f28-aecd-a65bb3acbcc6 | x | X / xAI | hackerone | True | 19 | False | not selected: run pinned to explicit program selector(s) |
| d02d8d9d-6710-4541-bf15-d879ad576d57 | concretecms | Concrete CMS | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 6d92bab8-17ed-4ec2-8c2a-c03568902be0 | priceline | Priceline | hackerone | True | 13 | False | not selected: run pinned to explicit program selector(s) |
| 5be1220b-10c0-493b-9d5c-71074b2293f1 | linkedin | LinkedIn | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 00a723ee-9344-4cc9-b4e8-11cf6399561b | vimeo | Vimeo | hackerone | True | 36 | False | not selected: run pinned to explicit program selector(s) |
| 312a3f8d-e1cf-41cb-aeee-675394c382f9 | wordpress | WordPress | hackerone | True | 21 | False | not selected: run pinned to explicit program selector(s) |
| 674be257-de51-4e18-9fb1-0cc22d452be3 | mavenlink | Mavenlink | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 0d4b6dd8-e549-49c6-9e96-9998a1ead185 | cloudflare | Cloudflare Public Bug Bounty | hackerone | True | 53 | False | not selected: run pinned to explicit program selector(s) |
| 90bb2cf8-611e-4402-9b95-0fd48da13cd3 | django | Django | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| d2b21e99-28bb-42e7-83dd-fd037591912e | rails | Ruby on Rails | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 74f5a1d2-4f91-4456-8a27-624630b4e2ff | phabricator | Phabricator | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 6976c79f-23d5-4d8a-a098-402e9ce565ad | security | HackerOne | hackerone | True | 27 | False | not selected: run pinned to explicit program selector(s) |
| 20a3f8b9-725b-46dc-8047-3ebf448d7ca0 | getyourguide_vdp | GetYourGuide VDP | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 9491bcff-8ebc-4ff3-b80f-9837ec65b5c1 | tines_automation_vdp | Tines (VDP) | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| ca6af4e6-e99a-4597-90df-03b33fd08be1 | mod_supply_chain_vdp | MOD Supply Chain VDP | hackerone | True | 181 | False | not selected: run pinned to explicit program selector(s) |
| 71eef50f-6fd0-4187-b44f-d09aa0250690 | vercel_platform_protection | Vercel Platform Protection | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| dd215241-281e-4ac0-bdbc-15f9bb02a6af | anduril_industries | Anduril Industries | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| 81835478-3086-4404-92c5-27f9804a2ce7 | bose_vdp | Bose (VDP) | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| db03a241-1e8e-488a-8bd1-aec902998195 | twilio | Twilio | hackerone | True | 24 | False | not selected: run pinned to explicit program selector(s) |
| 7074d761-490b-4a77-a304-f546007271f2 | doordash | DoorDash | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| b71d924c-c4bd-4a49-82f4-f8a2556b8caa | mueller_water_products_vdp | Mueller Water Products (VDP) | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| eb40acd0-f779-475d-80ea-c9fdb0a1a379 | henkel_vdp | Henkel | hackerone | True | 238 | False | not selected: run pinned to explicit program selector(s) |
| 61230f7b-3e94-47d9-a8cd-e1c0ce7cec50 | vueling_vdp | Vueling | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| a6a37658-6a42-4d09-b9b4-4ba126f96cbe | mufg-vdp | MUFG VDP | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| c0befe94-1936-4836-a946-de19a2ce1252 | docusign | DocuSign | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 2d3a7473-f4f8-456d-885d-f9e424cdd59b | bankunited | BankUnited | hackerone | True | 20 | False | not selected: run pinned to explicit program selector(s) |
| 05017cf3-58ea-4e1d-a395-fcb7070dc85a | robinhood | Robinhood Markets Bounty | hackerone | True | 25 | False | not selected: run pinned to explicit program selector(s) |
| 566e804b-3b3f-4a4f-9792-5b281b4fe452 | robinhood_markets | Robinhood Markets | hackerone | True | 30 | False | not selected: run pinned to explicit program selector(s) |
| 269ae4bc-7288-430b-ba25-b2e3d27f7ce5 | british_airways_vdp | British Airways VDP | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| b38da6f5-2520-4f81-8d51-06070b5506e7 | regions_financial | Regions Financial | hackerone | True | 13 | False | not selected: run pinned to explicit program selector(s) |
| 898ecc5e-ebb5-4184-a91b-4265bc268287 | vercel-open-source | Vercel Open Source | hackerone | True | 17 | False | not selected: run pinned to explicit program selector(s) |
| be6e6a40-e4a2-4e2c-941e-423623e07213 | netscaler_public_program | NetScaler Public Program | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 219153aa-9f2c-494f-b732-9ae6f19f8c40 | lovable-vdp | Lovable VDP | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 8ee0cbcf-d004-49ea-b4ea-0daf7ba4a875 | hack_the_box | Hack The Box | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| e3b68177-7ca2-4e06-aa91-e659fa16ab55 | banco_plata | Banco Plata | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| c89c44b3-effd-420d-85d5-eaca86b16f70 | braze_inc | Braze, Inc. | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 8e039c2b-5818-427d-842e-fe41296439fd | meesho_bbp | Meesho | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| ed003630-9af7-4fe8-9b86-85d8b01310d7 | tucows_vdp | Tucows (VDP) | hackerone | True | 11 | False | not selected: run pinned to explicit program selector(s) |
| 72f31304-df63-4111-a782-adb5265d893d | tbs-sct | Treasury Board of Canada Secretariat/Secrétariat du Conseil du Trésor du Canada | hackerone | True | 15 | False | not selected: run pinned to explicit program selector(s) |
| ede248e5-c509-4303-9c15-ab92e2f99726 | citi_group | Citi Group | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| d593f81d-5dcc-4468-9414-7bff84945854 | kong | Kong | hackerone | True | 14 | False | not selected: run pinned to explicit program selector(s) |
| abb7a82c-e1a3-4027-9c66-cd54bbb88a2b | worldpay | Worldpay | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| a84a19cd-a660-4c27-8d99-61ddcb8c1706 | hertz | Hertz VDP | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| d4f4c704-eb42-484f-a64d-e014309a803b | experian | Experian | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 3a98f922-9f3b-4452-9935-86dc848fd697 | hexagon_vdp | Hexagon-VDP | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| feac897b-3b3b-447d-b294-4927de2c5439 | eightfold | Eightfold | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 86690668-6516-4cd6-8a4e-5cbc36537d18 | centene_vdp | Centene_vdp | hackerone | True | 18 | False | not selected: run pinned to explicit program selector(s) |
| 295207d7-35d1-4dc4-921d-143042ce2e16 | msci | MSCI | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 194506a4-1aa2-4b9d-85e3-e2c9bb4960ff | ferrero | Ferrero | hackerone | True | 274 | False | not selected: run pinned to explicit program selector(s) |
| e0089518-eccf-4d5d-9c25-6209c6931ba9 | dust | Dust | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 5e3b7b5e-d2f4-41dc-9840-e6a9f01fb64c | hotmartvdp | Hotmart (VDP) | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 0155f17e-a3e0-4691-86b0-3ff294ba1ba7 | hex | Hex | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 77474b31-fdaa-4f8d-82cf-408ff1761ed9 | hyland_software | Hyland Software | hackerone | True | 14 | False | not selected: run pinned to explicit program selector(s) |

### Program Scope Used
| scope_type | asset_type | value | notes |
| --- | --- | --- | --- |
| in_scope | domain | hosted.weblate.org | Please use the [Sandbox translation project](https://hosted.weblate.org/projects/sandbox/) for testing. |
| in_scope | url | https://github.com/WeblateOrg/docker |  |
| in_scope | url | https://github.com/WeblateOrg/translation-finder |  |
| in_scope | url | https://github.com/WeblateOrg/weblate |  |
| in_scope | url | https://github.com/WeblateOrg/website |  |
| in_scope | url | https://github.com/WeblateOrg/wlc |  |
| out_of_scope | domain | github.com | The GitHub wiki is intentionally open to public. |
| out_of_scope | domain | hg.weblate.org | This site has intentional setup this way to allow mercurial client to clone the repository. |

## Service Health
| service | http_status | health_status | error |
| --- | --- | --- | --- |
| scraper | 200 | healthy |  |
| core-engine | 200 | healthy |  |
| reporter |  |  | All connection attempts failed |
| attack-graph-engine |  |  | All connection attempts failed |
| api-gateway | 200 | healthy |  |

## Scan Summary
### Start Response
```json
{
  "payload": {
    "program_id": "2715b22b-3506-4fb1-bece-95cad2eec341",
    "scan_id": "ccc0a3c6-a203-4333-a6dc-b54608d8393e",
    "status": "queued"
  },
  "status_code": 200
}
```

### Final Scan Row
```json
{
  "completed_at": "2026-03-25T03:33:29.431849+00:00",
  "created_at": "2026-03-25T03:32:40.783338+00:00",
  "error_detail": null,
  "finding_count": 0,
  "partial_detail": "{\"errors\": {\"nuclei_scan\": \"nuclei exited with code 2. stderr: \"}, \"failed_stages\": [\"nuclei_scan\"]}",
  "program_id": "2715b22b-3506-4fb1-bece-95cad2eec341",
  "retry_count": 0,
  "scan_id": "ccc0a3c6-a203-4333-a6dc-b54608d8393e",
  "severity_breakdown": "{\"low\": 0, \"high\": 0, \"info\": 0, \"medium\": 0, \"critical\": 0}",
  "started_at": "2026-03-25T03:32:40.783338+00:00",
  "status": "partial"
}
```

### Scan Wait Result
```json
{
  "status_at_snapshot": "partial",
  "terminal_reached": true,
  "timeout_seconds": 3600
}
```

### Pipeline Stage Timeline
| stage_number | stage_name | status | started_at | completed_at | error_detail |
| --- | --- | --- | --- | --- | --- |
| 1.0 | asset_discovery | completed | 2026-03-25T03:32:51.907487+00:00 | 2026-03-25T03:33:26.388829+00:00 |  |
| 2.0 | fingerprinting | completed | 2026-03-25T03:33:26.391529+00:00 | 2026-03-25T03:33:27.792702+00:00 |  |
| 3.0 | enumeration | completed | 2026-03-25T03:33:27.794295+00:00 | 2026-03-25T03:33:28.536848+00:00 |  |
| 4.0 | nuclei_scan | failed | 2026-03-25T03:33:27.794298+00:00 | 2026-03-25T03:33:29.422094+00:00 | nuclei exited with code 2. stderr:  |
| 5.0 | web_vuln_tests | completed | 2026-03-25T03:33:28.540149+00:00 | 2026-03-25T03:33:29.426259+00:00 |  |
| 6.0 | js_secrets | completed | 2026-03-25T03:33:28.540221+00:00 | 2026-03-25T03:33:29.429093+00:00 |  |
| 10.1 | report_handoff | completed | 2026-03-25T03:33:29.434062+00:00 | 2026-03-25T03:33:29.441153+00:00 |  |

### Artifact Counts
```json
{
  "assets_count": 2,
  "endpoints_count": 6,
  "evidence_count": 0,
  "findings_count": 0,
  "js_assets_count": 0
}
```

### Findings by Severity
_None_

### Findings by Source
_None_

### Detailed Findings
_None_

## Queue and Worker Evidence
### Core DLQ Inspect API
```json
{
  "payload": {
    "queues": [
      {
        "consumers": 1,
        "exists": true,
        "messages": 0,
        "queue": "scan.jobs"
      },
      {
        "consumers": 0,
        "exists": true,
        "messages": 0,
        "queue": "scan.jobs.dlq"
      },
      {
        "consumers": 1,
        "exists": true,
        "messages": 0,
        "queue": "report.jobs"
      },
      {
        "consumers": 0,
        "exists": true,
        "messages": 0,
        "queue": "report.jobs.dlq"
      }
    ]
  },
  "status_code": 200,
  "url": "http://localhost:8002/api/v1/queue/dlq/inspect"
}
```

### Queue Baseline Purge
```json
{
  "attempts": [
    {
      "ok": true,
      "purge_error": null,
      "purge_status_code": 204,
      "queue": "scan.jobs",
      "ready_after": 0,
      "ready_before": 0,
      "state_after": {
        "consumers": 1,
        "exists": true,
        "messages": 0,
        "messages_ready": 0,
        "messages_unacknowledged": 0,
        "queue": "scan.jobs",
        "status_code": 200
      },
      "state_before": {
        "consumers": 1,
        "exists": true,
        "messages": 0,
        "messages_ready": 0,
        "messages_unacknowledged": 0,
        "queue": "scan.jobs",
        "status_code": 200
      },
      "unacked_after": 0,
      "unacked_before": 0
    },
    {
      "ok": true,
      "purge_error": null,
      "purge_status_code": 204,
      "queue": "scan.jobs",
      "ready_after": 0,
      "ready_before": 0,
      "state_after": {
        "consumers": 1,
        "exists": true,
        "messages": 0,
        "messages_ready": 0,
        "messages_unacknowledged": 0,
        "queue": "scan.jobs",
        "status_code": 200
      },
      "state_before": {
        "consumers": 1,
        "exists": true,
        "messages": 0,
        "messages_ready": 0,
        "messages_unacknowledged": 0,
        "queue": "scan.jobs",
        "status_code": 200
      },
      "unacked_after": 0,
      "unacked_before": 0
    }
  ],
  "enabled": true,
  "final_state": {
    "consumers": 1,
    "exists": true,
    "messages": 0,
    "messages_ready": 0,
    "messages_unacknowledged": 0,
    "queue": "scan.jobs",
    "status_code": 200
  },
  "initial_state": {
    "consumers": 1,
    "exists": true,
    "messages": 0,
    "messages_ready": 0,
    "messages_unacknowledged": 0,
    "queue": "scan.jobs",
    "status_code": 200
  },
  "ok": true,
  "queue": "scan.jobs",
  "settle_poll_seconds": 5.0,
  "settle_state": {
    "consumers": 1,
    "exists": true,
    "messages": 0,
    "messages_ready": 0,
    "messages_unacknowledged": 0,
    "queue": "scan.jobs",
    "status_code": 200
  },
  "settle_timeout_seconds": 60,
  "settled_unacked": true
}
```

### Queue Baseline Wait
```json
{
  "reached": true,
  "seconds_waited": 0.0,
  "state": {
    "consumers": 1,
    "exists": true,
    "messages": 0,
    "messages_ready": 0,
    "messages_unacknowledged": 0,
    "queue": "scan.jobs",
    "status_code": 200
  },
  "timeout_seconds": 60
}
```

### RabbitMQ Queue States
| queue | exists | messages | ready | unacked | consumers | http_status | error |
| --- | --- | --- | --- | --- | --- | --- | --- |
| scan.jobs | True | 0 | 0 | 0 | 1 |  |  |
| scan.jobs.dlq | True | 0 | 0 | 0 | 0 |  |  |
| browser.jobs | True | 0 | 0 | 0 | 1 |  |  |
| browser.jobs.dlq | True | 0 | 0 | 0 | 0 |  |  |
| api.fuzz.jobs | True | 0 | 0 | 0 | 1 |  |  |
| api.fuzz.jobs.dlq | True | 0 | 0 | 0 | 0 |  |  |
| js.analysis.jobs | True | 0 | 0 | 0 | 1 |  |  |
| js.analysis.jobs.dlq | True | 0 | 0 | 0 | 0 |  |  |
| scenario.jobs | True | 0 | 0 | 0 | 1 |  |  |
| scenario.jobs.dlq | True | 0 | 0 | 0 | 0 |  |  |
| verify.jobs | True | 0 | 0 | 0 | 1 |  |  |
| verify.jobs.dlq | True | 0 | 0 | 0 | 0 |  |  |
| ai.analysis.jobs | True | 0 | 0 | 0 | 1 |  |  |
| ai.analysis.jobs.dlq | True | 0 | 0 | 0 | 0 |  |  |
| report.jobs | True | 0 | 0 | 0 | 1 |  |  |
| report.jobs.dlq | True | 0 | 0 | 0 | 0 |  |  |
| reports.completed | True | 0 | 0 | 0 | 0 |  |  |

## API Snapshots
### /scans/{scan_id}
```json
{
  "payload": {
    "completed_at": "2026-03-25T03:33:29.431849+00:00",
    "error_detail": null,
    "finding_count": 0,
    "program_id": "2715b22b-3506-4fb1-bece-95cad2eec341",
    "scan_id": "ccc0a3c6-a203-4333-a6dc-b54608d8393e",
    "severity_breakdown": {
      "critical": 0,
      "high": 0,
      "info": 0,
      "low": 0,
      "medium": 0
    },
    "started_at": "2026-03-25T03:32:40.783338+00:00",
    "status": "partial"
  },
  "status_code": 200,
  "url": "http://localhost:8002/api/v1/scans/ccc0a3c6-a203-4333-a6dc-b54608d8393e"
}
```

### /scans/{scan_id}/findings
```json
{
  "payload": {
    "count": 0,
    "findings": []
  },
  "status_code": 200,
  "url": "http://localhost:8002/api/v1/scans/ccc0a3c6-a203-4333-a6dc-b54608d8393e/findings"
}
```

## Forced Deep Trace (Downstream Replay)
_Not executed._

## Process Evidence
### Command: docker compose up -d
- Return code: `0`
- Command: `docker compose -f C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1\infra\docker-compose.yml --env-file C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1\.env up -d`

```text
STDOUT:
<empty>

STDERR:
 Container attackbot-redis-1 Running 
 Container attackbot-neo4j-1 Running 
 Container attackbot-rabbitmq-1 Running 
 Container attackbot-vault-1 Running 
 Container attackbot-minio-1 Running 
 Container attackbot-postgres-1 Running 
 Container attackbot-loki-1 Running 
 Container attackbot-prometheus-1 Running 
 Container attackbot-core-engine-1 Running 
 Container attackbot-grafana-1 Running 
 Container attackbot-reporter-1 Running 
 Container attackbot-scraper-1 Running 
 Container attackbot-scenario-runner-1 Running 
 Container attackbot-attack-graph-engine-1 Running 
 Container attackbot-js-analysis-worker-1 Running 
 Container attackbot-ai-analysis-worker-1 Running 
 Container attackbot-api-fuzzer-worker-1 Running 
 Container attackbot-exploit-verifier-1 Running 
 Container attackbot-browser-worker-1 Running 
 Container attackbot-reporter-worker-1 Running 
 Container attackbot-api-gateway-1 Running 
 Container attackbot-core-worker-1 Running 
 Container attackbot-tempo-1 Starting 
 Container attackbot-minio-1 Waiting 
 Container attackbot-postgres-1 Waiting 
 Container attackbot-vault-1 Waiting 
 Container attackbot-tempo-1 Started 
 Container attackbot-postgres-1 Healthy 
 Container attackbot-migrate-1 Starting 
 Container attackbot-minio-1 Healthy 
 Container attackbot-vault-1 Healthy 
 Container attackbot-minio-init-1 Starting 
 Container attackbot-vault-init-1 Starting 
 Container attackbot-migrate-1 Started 
 Container attackbot-migrate-1 Waiting 
 Container attackbot-neo4j-1 Waiting 
 Container attackbot-minio-init-1 Started 
 Container attackbot-migrate-1 Waiting 
 Container attackbot-minio-init-1 Waiting 
 Container attackbot-postgres-1 Waiting 
 Container attackbot-redis-1 Waiting 
 Container attackbot-minio-init-1 Waiting 
 Container attackbot-postgres-1 Waiting 
 Container attackbot-redis-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-migrate-1 Waiting 
 Container attackbot-minio-init-1 Waiting 
 Container attackbot-postgres-1 Waiting 
 Container attackbot-redis-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-migrate-1 Waiting 
 Container attackbot-vault-init-1 Started 
 Container attackbot-neo4j-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-minio-init-1 Exited 
 Container attackbot-postgres-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-redis-1 Healthy 
 Container attackbot-minio-init-1 Exited 
 Container attackbot-redis-1 Healthy 
 Container attackbot-minio-init-1 Exited 
 Container attackbot-redis-1 Healthy 
 Container attackbot-postgres-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-postgres-1 Healthy 
 Container attackbot-migrate-1 Exited 
 Container attackbot-migrate-1 Exited 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-migrate-1 Exited 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-redis-1 Waiting 
 Container attackbot-migrate-1 Exited 
 Container attackbot-reporter-1 Waiting 
 Container attackbot-attack-graph-engine-1 Waiting 
 Container attackbot-scraper-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-reporter-1 Waiting 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-redis-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-reporter-1 Healthy 
 Container attackbot-attack-graph-engine-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-scraper-1 Healthy 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-reporter-1 Healthy 

```

### Command: docker compose ps
- Return code: `0`
- Command: `docker compose -f C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1\infra\docker-compose.yml --env-file C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1\.env ps`

```text
STDOUT:
NAME                              IMAGE                           COMMAND                  SERVICE               CREATED          STATUS                          PORTS
attackbot-ai-analysis-worker-1    attackbot-ai-analysis-worker    "celery -A backend.sâ€¦"   ai-analysis-worker    9 minutes ago    Up 9 minutes                    
attackbot-api-fuzzer-worker-1     attackbot-api-fuzzer-worker     "celery -A backend.sâ€¦"   api-fuzzer-worker     9 minutes ago    Up 9 minutes                    
attackbot-api-gateway-1           attackbot-api-gateway           "uvicorn backend.serâ€¦"   api-gateway           46 minutes ago   Up 45 minutes (unhealthy)       0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
attackbot-attack-graph-engine-1   attackbot-attack-graph-engine   "uvicorn backend.serâ€¦"   attack-graph-engine   46 minutes ago   Up 45 minutes (healthy)         8006/tcp
attackbot-browser-worker-1        attackbot-browser-worker        "celery -A backend.sâ€¦"   browser-worker        9 minutes ago    Up 9 minutes                    
attackbot-core-engine-1           attackbot-core-engine           "uvicorn backend.serâ€¦"   core-engine           6 minutes ago    Up 6 minutes (healthy)          0.0.0.0:8002->8002/tcp, [::]:8002->8002/tcp
attackbot-core-worker-1           attackbot-core-worker           "celery -A backend.sâ€¦"   core-worker           6 minutes ago    Up 5 minutes                    8002/tcp
attackbot-exploit-verifier-1      attackbot-exploit-verifier      "celery -A backend.sâ€¦"   exploit-verifier      9 minutes ago    Up 9 minutes                    
attackbot-grafana-1               grafana/grafana:latest          "/run.sh"                grafana               46 minutes ago   Up 46 minutes                   0.0.0.0:3000->3000/tcp, [::]:3000->3000/tcp
attackbot-js-analysis-worker-1    attackbot-js-analysis-worker    "celery -A backend.sâ€¦"   js-analysis-worker    9 minutes ago    Up 9 minutes                    
attackbot-loki-1                  grafana/loki:latest             "/usr/bin/loki -confâ€¦"   loki                  46 minutes ago   Up 46 minutes                   3100/tcp
attackbot-minio-1                 minio/minio                     "/usr/bin/docker-entâ€¦"   minio                 46 minutes ago   Up 46 minutes (healthy)         9000/tcp
attackbot-neo4j-1                 neo4j:5-community               "tini -g -- /startupâ€¦"   neo4j                 46 minutes ago   Up 46 minutes (healthy)         7473-7474/tcp, 7687/tcp
attackbot-postgres-1              postgres:16                     "docker-entrypoint.sâ€¦"   postgres              46 minutes ago   Up 46 minutes (healthy)         0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp
attackbot-prometheus-1            prom/prometheus:latest          "/bin/prometheus --câ€¦"   prometheus            46 minutes ago   Up 46 minutes                   9090/tcp
attackbot-rabbitmq-1              rabbitmq:3-management           "docker-entrypoint.sâ€¦"   rabbitmq              46 minutes ago   Up 46 minutes (healthy)         0.0.0.0:15672->15672/tcp, [::]:15672->15672/tcp
attackbot-redis-1                 redis:7-alpine                  "docker-entrypoint.sâ€¦"   redis                 46 minutes ago   Up 46 minutes (healthy)         6379/tcp
attackbot-reporter-1              attackbot-reporter              "uvicorn backend.serâ€¦"   reporter              9 minutes ago    Up 9 minutes (healthy)          8003/tcp
attackbot-reporter-worker-1       attackbot-reporter-worker       "celery -A backend.sâ€¦"   reporter-worker       9 minutes ago    Up 9 minutes                    8003/tcp
attackbot-scenario-runner-1       attackbot-scenario-runner       "celery -A backend.sâ€¦"   scenario-runner       9 minutes ago    Up 9 minutes                    
attackbot-scraper-1               attackbot-scraper               "uvicorn backend.serâ€¦"   scraper               46 minutes ago   Up 45 minutes (healthy)         0.0.0.0:8001->8001/tcp, [::]:8001->8001/tcp
attackbot-tempo-1                 grafana/tempo:latest            "/tempo"                 tempo                 46 minutes ago   Restarting (1) 14 seconds ago   
attackbot-vault-1                 hashicorp/vault:1.15            "docker-entrypoint.sâ€¦"   vault                 46 minutes ago   Up 46 minutes (healthy)         8200/tcp


STDERR:
<empty>
```

### Command: docker compose logs (tail 300)
- Return code: `0`
- Command: `docker compose -f C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1\infra\docker-compose.yml --env-file C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1\.env logs --no-color --since 2026-03-25T03:32:40Z --tail 300 scraper core-engine core-worker reporter reporter-worker`

```text
STDOUT:
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/programs/2715b22b-3506-4fb1-bece-95cad2eec341 "HTTP/1.1 200 OK"
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/programs/2715b22b-3506-4fb1-bece-95cad2eec341/scope "HTTP/1.1 200 OK"
core-engine-1  | {"scan_id": "ccc0a3c6-a203-4333-a6dc-b54608d8393e", "program_id": "2715b22b-3506-4fb1-bece-95cad2eec341", "event": "Scan created", "service": "core-engine", "level": "info", "timestamp": "2026-03-25T03:32:40.790026Z"}
core-engine-1  | {"check": "nuclei", "detail": "/usr/local/bin/nuclei", "event": "worker_toolchain_check_ok", "service": "core-engine", "level": "info", "timestamp": "2026-03-25T03:32:51.567662Z"}
core-engine-1  | {"check": "nuclei_templates", "detail": null, "event": "worker_toolchain_check_ok", "service": "core-engine", "level": "info", "timestamp": "2026-03-25T03:32:51.567791Z"}
core-engine-1  | INFO:     172.18.0.1:44366 - "POST /api/v1/scans/start HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.18.0.8:40338 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:47784 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.18.0.8:57712 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:42788 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:37656 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.18.0.8:58538 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:37964 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.18.0.8:51500 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1  | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1  | INFO:     127.0.0.1:41700 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.18.0.1:50528 - "GET /api/v1/scans/ccc0a3c6-a203-4333-a6dc-b54608d8393e HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.18.0.1:50544 - "GET /api/v1/scans/ccc0a3c6-a203-4333-a6dc-b54608d8393e/findings HTTP/1.1" 200 OK
core-engine-1  | INFO:     172.18.0.1:50548 - "GET /api/v1/queue/dlq/inspect HTTP/1.1" 200 OK
scraper-1      | {"handle": "kartpay", "program_id": "66413d4b-7261-4f5c-9f64-a371bc21cb88", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:32:40.005139Z"}
scraper-1      | INFO:     172.18.0.12:39406 - "GET /api/v1/programs/2715b22b-3506-4fb1-bece-95cad2eec341 HTTP/1.1" 200 OK
scraper-1      | INFO:     172.18.0.12:39406 - "GET /api/v1/programs/2715b22b-3506-4fb1-bece-95cad2eec341/scope HTTP/1.1" 200 OK
scraper-1      | {"handle": "netlify", "program_id": "22a25565-81f2-4a37-ad8f-fb045a3c73de", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:32:42.631048Z"}
scraper-1      | {"handle": "nodejs", "program_id": "ba21f266-0ba2-4f60-a068-760f68d8e508", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:32:44.617080Z"}
scraper-1      | {"handle": "deconf_com", "program_id": "ed83250d-2e93-42d8-8f94-596482f33b21", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:32:46.185139Z"}
scraper-1      | {"handle": "epicgames", "program_id": "255a402e-6016-4212-b307-c398bfeb17f5", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:32:48.842010Z"}
scraper-1      | INFO:     127.0.0.1:60756 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | {"handle": "valve", "program_id": "bfa87224-c620-460a-a07c-94e3cf3f33fa", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:32:50.900655Z"}
scraper-1      | INFO:     172.18.0.12:57780 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | INFO:     172.18.0.20:48990 - "GET /api/v1/programs/2715b22b-3506-4fb1-bece-95cad2eec341/scope HTTP/1.1" 200 OK
scraper-1      | {"handle": "elastic", "program_id": "10e76933-dd6b-4114-854e-8b0b395324e6", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:32:52.780293Z"}
scraper-1      | INFO:     172.18.0.8:58172 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | {"handle": "fig", "program_id": "277308ca-9abb-4906-bbaa-0b498d38deb4", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:32:54.445364Z"}
scraper-1      | {"handle": "smule", "program_id": "badbf9e1-50b3-4c59-be6a-367c9349997a", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:32:56.082419Z"}
scraper-1      | {"handle": "bitmex", "program_id": "753a8c4b-fb2d-4ab6-8a46-015ea03ce88b", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:32:57.669703Z"}
scraper-1      | {"handle": "ed", "program_id": "fc367bed-7427-484f-ade9-0890a4600de7", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:32:59.457155Z"}
scraper-1      | INFO:     127.0.0.1:52604 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | {"handle": "jamieweb", "program_id": "037357c4-8fa2-4be1-ab2a-da0fbe6efc97", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:33:01.145968Z"}
scraper-1      | INFO:     172.18.0.12:43472 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | {"handle": "flutteruki", "program_id": "3b5d0d6c-e569-48b0-bda4-06b210723f13", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:33:02.980787Z"}
scraper-1      | {"handle": "databricks", "program_id": "5ce15f4b-c524-4294-bd03-13ce89a39e07", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:33:05.067601Z"}
scraper-1      | {"handle": "cosmos", "program_id": "acf12102-204a-49dd-9049-43eadf8d0b1e", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:33:06.718199Z"}
scraper-1      | {"handle": "coalition", "program_id": "2be2da2e-9195-4ba0-9f3d-b40cb3f43fd2", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:33:08.675603Z"}
scraper-1      | INFO:     172.18.0.8:39640 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | INFO:     127.0.0.1:49282 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | {"handle": "affirm", "program_id": "fea3b05f-4661-4526-b96a-af85aa292079", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:33:11.141822Z"}
scraper-1      | INFO:     172.18.0.12:43976 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | {"handle": "crowdstrike", "program_id": "9d100afb-a52e-469e-851c-09f2f5ac4f8e", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:33:12.784065Z"}
scraper-1      | {"handle": "pingidentity", "program_id": "a7a0c645-708d-404a-8590-613ca77a7b83", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:33:14.450115Z"}
scraper-1      | {"handle": "passhash", "program_id": "2d226257-e92a-49f9-8c61-eb8c6d4f5822", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:33:16.273469Z"}
scraper-1      | {"handle": "ycombinator", "program_id": "1167bea8-d2cd-4871-80ca-1214fd5642d7", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:33:18.071709Z"}
scraper-1      | {"handle": "ratelimited", "program_id": "5416cfb5-f515-4942-b462-86bc3793a29a", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:33:19.146467Z"}
scraper-1      | INFO:     127.0.0.1:54074 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | {"handle": "crypto", "program_id": "25350a62-076d-4c10-997b-320e56a20985", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:33:20.819958Z"}
scraper-1      | INFO:     172.18.0.12:59896 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | {"handle": "liberapay", "program_id": "c638b22f-1628-4ef9-ae59-5b0ca6095294", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:33:22.844337Z"}
scraper-1      | INFO:     172.18.0.8:44068 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1      | {"handle": "pixiv", "program_id": "b56553b9-aeb5-4c4a-84f2-adeafedf752a", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:33:25.283714Z"}
scraper-1      | {"handle": "arkadiyt-projects", "program_id": "de21d0c4-3f44-4221-820e-944dece653e3", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:33:26.861830Z"}
scraper-1      | {"handle": "s-pankki", "program_id": "d0110b57-0c64-4e1f-895a-a2b4ac670646", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:33:28.899856Z"}
scraper-1      | {"handle": "hannob", "program_id": "2706bda2-b193-4221-8eb7-84c24e02ebc0", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:33:29.963552Z"}
scraper-1      | INFO:     127.0.0.1:50346 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | {"handle": "chaturbate", "program_id": "bfec31eb-2bab-4da8-bdec-25e63b8334f8", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:33:31.616366Z"}
scraper-1      | INFO:     172.18.0.12:41696 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1      | {"handle": "cfptime", "program_id": "e648519e-ea02-4b28-b27f-fe0109f03f4b", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:33:33.294964Z"}
scraper-1      | {"handle": "marriott", "program_id": "844d2936-547e-44fd-92d7-efd82557ad5b", "event": "program_upserted", "service": "scraper", "level": "info", "timestamp": "2026-03-25T03:33:37.544955Z"}
scraper-1      | INFO:     172.18.0.8:51676 - "GET /metrics HTTP/1.1" 404 Not Found
core-worker-1  | [2026-03-25 03:32:51,703: INFO/MainProcess] Task core_engine.scan_task[f33f5ede-0d3e-4aa8-8a24-964e75dbb0a1] received
core-worker-1  | [2026-03-25 03:32:51,709: WARNING/ForkPoolWorker-2] {"program_id": "2715b22b-3506-4fb1-bece-95cad2eec341", "event_type": "program.scraped", "event": "Scan task received", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:32:51.708921Z"}
core-worker-1  | [2026-03-25 03:32:51,824: WARNING/ForkPoolWorker-2] {"pool_size": 10, "max_overflow": 20, "event": "db_initialized", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:32:51.824436Z"}
core-worker-1  | [2026-03-25 03:32:51,825: WARNING/ForkPoolWorker-2] {"endpoint": "minio:9000", "secure": false, "event": "minio_connected", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:32:51.825640Z"}
core-worker-1  | [2026-03-25 03:32:51,874: WARNING/ForkPoolWorker-2] {"scan_id": "ccc0a3c6-a203-4333-a6dc-b54608d8393e", "event": "Resuming existing scan", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:32:51.873989Z"}
core-worker-1  | [2026-03-25 03:32:51,896: INFO/ForkPoolWorker-2] HTTP Request: GET http://scraper:8001/api/v1/programs/2715b22b-3506-4fb1-bece-95cad2eec341/scope "HTTP/1.1 200 OK"
core-worker-1  | [2026-03-25 03:32:51,907: WARNING/ForkPoolWorker-2] {"url": "amqp://attackbot:attackbot@rabbitmq:5672/", "event": "queue_publisher_connected", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:32:51.906950Z"}
reporter-worker-1  | [2026-03-25 03:33:29,437: WARNING/MainProcess] {"queue": "report.jobs", "event_id": "95ef6da7-b595-4668-a9dc-9e87a649cd09", "event_type": "scan.completed", "scan_id": "ccc0a3c6-a203-4333-a6dc-b54608d8393e", "program_id": "2715b22b-3506-4fb1-bece-95cad2eec341", "finding_count": 0, "severity_breakdown": {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}, "event": "report_job_received", "service": "reporter-worker", "level": "info", "timestamp": "2026-03-25T03:33:29.437547Z"}
reporter-worker-1  | [2026-03-25 03:33:29,438: WARNING/MainProcess] {"scan_id": "ccc0a3c6-a203-4333-a6dc-b54608d8393e", "formats_requested": ["pdf", "docx"], "include_evidence_screenshots": true, "event": "report_job_formats_requested", "service": "reporter-worker", "level": "info", "timestamp": "2026-03-25T03:33:29.438250Z"}
core-worker-1      | [2026-03-25 03:32:51,907: WARNING/ForkPoolWorker-2] {"scan_id": "ccc0a3c6-a203-4333-a6dc-b54608d8393e", "event": "Stage 0: Scope filter", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:32:51.907160Z"}
core-worker-1      | [2026-03-25 03:32:51,907: WARNING/ForkPoolWorker-2] {"in_scope_count": 6, "out_of_scope_count": 2, "event": "ScopeFilter built", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:32:51.907403Z"}
core-worker-1      | [2026-03-25 03:32:51,908: WARNING/ForkPoolWorker-2] {"scan_id": "ccc0a3c6-a203-4333-a6dc-b54608d8393e", "skipped_counts": {"url_host_not_domain_led": 5, "explicit_target_out_of_scope": 5}, "event": "asset_discovery_seed_scope_skipped", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:32:51.908139Z"}
core-worker-1      | [2026-03-25 03:32:51,908: WARNING/ForkPoolWorker-2] {"args": "subfinder", "timeout": 180, "event": "Running subfinder[hosted.weblate.org]", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:32:51.908897Z"}
core-worker-1      | [2026-03-25 03:33:22,670: WARNING/ForkPoolWorker-2] {"domain": "hosted.weblate.org", "event": "alterx_skipped_no_subfinder_results", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:33:22.670163Z"}
core-worker-1      | [2026-03-25 03:33:22,670: WARNING/ForkPoolWorker-2] {"args": "dnsx", "timeout": 270, "event": "Running dnsx[hosted.weblate.org]", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:33:22.670696Z"}
core-worker-1      | [2026-03-25 03:33:23,415: WARNING/ForkPoolWorker-2] {"args": "httpx", "timeout": 180, "event": "Running httpx[hosted.weblate.org]", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:33:23.415736Z"}
core-worker-1      | [2026-03-25 03:33:24,972: WARNING/ForkPoolWorker-2] {"args": "httpx", "timeout": 180, "event": "Running httpx[explicit_scope]", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:33:24.972748Z"}
core-worker-1      | [2026-03-25 03:33:26,381: WARNING/ForkPoolWorker-2] {"scan_id": "ccc0a3c6-a203-4333-a6dc-b54608d8393e", "seed_domains": 1, "explicit_targets": 1, "assets_found": 1, "errors": 0, "event": "Stage 1 complete", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:33:26.381278Z"}
core-worker-1      | [2026-03-25 03:33:26,391: WARNING/ForkPoolWorker-2] {"args": "httpx", "timeout": 180, "event": "Running httpx_fingerprint", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:33:26.391795Z"}
core-worker-1      | [2026-03-25 03:33:27,786: WARNING/ForkPoolWorker-2] {"scan_id": "ccc0a3c6-a203-4333-a6dc-b54608d8393e", "assets_enriched": 1, "event": "Stage 2 complete", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:33:27.786008Z"}
core-worker-1      | [2026-03-25 03:33:27,794: WARNING/ForkPoolWorker-2] {"args": "nuclei", "timeout": 1080, "event": "Running nuclei", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:33:27.794764Z"}
core-worker-1      | [2026-03-25 03:33:27,795: WARNING/ForkPoolWorker-2] {"args": "ffuf", "timeout": 540, "event": "Running ffuf[https://hosted.weblate.org]", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:33:27.795715Z"}
core-worker-1      | [2026-03-25 03:33:27,796: WARNING/ForkPoolWorker-2] {"domain": "hosted.weblate.org", "event": "waybackurls skipped via E2E flag", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:33:27.796556Z"}
core-worker-1      | [2026-03-25 03:33:27,881: WARNING/ForkPoolWorker-2] {"scan_id": "ccc0a3c6-a203-4333-a6dc-b54608d8393e", "return_code": 2, "reason_bucket": "nuclei_startup_initialization_failure", "target_count": 1, "sample_targets": ["https://hosted.weblate.org"], "error": "nuclei exited with code 2. stderr: ", "event": "nuclei_startup_failure_detected", "service": "core-worker", "level": "error", "timestamp": "2026-03-25T03:33:27.881078Z"}
core-worker-1      | [2026-03-25 03:33:28,525: WARNING/ForkPoolWorker-2] {"scan_id": "ccc0a3c6-a203-4333-a6dc-b54608d8393e", "endpoints": 6, "js_assets": 0, "event": "Stage 3 complete", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:33:28.525232Z"}
core-worker-1      | [2026-03-25 03:33:28,541: WARNING/ForkPoolWorker-2] {"scan_id": "ccc0a3c6-a203-4333-a6dc-b54608d8393e", "js_files_scanned": 0, "secrets_found": 0, "event": "Stage 6 complete", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T03:33:28.541120Z"}
core-worker-1      | [2026-03-25 03:33:28,914: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/robots.txt "HTTP/1.1 200 OK"
core-worker-1      | [2026-03-25 03:33:28,920: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/search "HTTP/1.1 301 Moved Permanently"
core-worker-1      | [2026-03-25 03:33:28,935: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/favicon.ico "HTTP/1.1 301 Moved Permanently"
core-worker-1      | [2026-03-25 03:33:28,955: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/user "HTTP/1.1 301 Moved Permanently"
core-worker-1      | [2026-03-25 03:33:28,960: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/sitemap.xml "HTTP/1.1 200 OK"
core-worker-1      | [2026-03-25 03:33:28,964: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/admin "HTTP/1.1 301 Moved Permanently"
core-worker-1      | [2026-03-25 03:33:29,042: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/robots.txt "HTTP/1.1 200 OK"
core-worker-1      | [2026-03-25 03:33:29,051: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/search "HTTP/1.1 301 Moved Permanently"
core-worker-1      | [2026-03-25 03:33:29,067: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/favicon.ico "HTTP/1.1 301 Moved Permanently"
reporter-worker-1  | [2026-03-25 03:33:29,438: WARNING/MainProcess] {"scan_id": "ccc0a3c6-a203-4333-a6dc-b54608d8393e", "program_id": "2715b22b-3506-4fb1-bece-95cad2eec341", "event": "report_generation_not_yet_implemented", "service": "reporter-worker", "level": "warning", "timestamp": "2026-03-25T03:33:29.438389Z"}
core-worker-1      | [2026-03-25 03:33:29,098: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/sitemap.xml "HTTP/1.1 200 OK"
core-worker-1      | [2026-03-25 03:33:29,105: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/user "HTTP/1.1 301 Moved Permanently"
core-worker-1      | [2026-03-25 03:33:29,114: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/admin "HTTP/1.1 301 Moved Permanently"
core-worker-1      | [2026-03-25 03:33:29,168: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/robots.txt "HTTP/1.1 200 OK"
core-worker-1      | [2026-03-25 03:33:29,178: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/search "HTTP/1.1 301 Moved Permanently"
core-worker-1      | [2026-03-25 03:33:29,196: INFO/ForkPoolWorker-2] HTTP Request: GET https://hosted.weblate.org/favicon.ico "HTTP/1.1 301 Moved Permanently"
core-worker-1      | [2026-03-25 03:33:29,235: INFO/
... [truncated]

STDERR:
<empty>
```

### Command: docker compose logs reporter-worker (tail 300)
- Return code: `0`
- Command: `docker compose -f C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1\infra\docker-compose.yml --env-file C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1\.env logs --no-color --since 2026-03-25T03:32:40Z --tail 300 reporter-worker`

```text
STDOUT:
reporter-worker-1  | [2026-03-25 03:33:29,437: WARNING/MainProcess] {"queue": "report.jobs", "event_id": "95ef6da7-b595-4668-a9dc-9e87a649cd09", "event_type": "scan.completed", "scan_id": "ccc0a3c6-a203-4333-a6dc-b54608d8393e", "program_id": "2715b22b-3506-4fb1-bece-95cad2eec341", "finding_count": 0, "severity_breakdown": {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}, "event": "report_job_received", "service": "reporter-worker", "level": "info", "timestamp": "2026-03-25T03:33:29.437547Z"}
reporter-worker-1  | [2026-03-25 03:33:29,438: WARNING/MainProcess] {"scan_id": "ccc0a3c6-a203-4333-a6dc-b54608d8393e", "formats_requested": ["pdf", "docx"], "include_evidence_screenshots": true, "event": "report_job_formats_requested", "service": "reporter-worker", "level": "info", "timestamp": "2026-03-25T03:33:29.438250Z"}
reporter-worker-1  | [2026-03-25 03:33:29,438: WARNING/MainProcess] {"scan_id": "ccc0a3c6-a203-4333-a6dc-b54608d8393e", "program_id": "2715b22b-3506-4fb1-bece-95cad2eec341", "event": "report_generation_not_yet_implemented", "service": "reporter-worker", "level": "warning", "timestamp": "2026-03-25T03:33:29.438389Z"}


STDERR:
<empty>
```

## Observed Gaps in Current Implementation
- Reporter worker currently validates `report.jobs` envelopes only.
- Specialist workers are queue listeners; deeper stages land in later milestones.
- This report reflects what ran in this test session, not aspirational docs.
