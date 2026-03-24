# AttackBot End-to-End Findings Report

- Generated at: `2026-03-24T00:13:40.447344+00:00`
- Report file: `E2E_SYSTEM_FINDINGS.md`
- Project root: `C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1`
- Test outcome: `failed`
- Error: `Scan start failed with status=500: Internal Server Error`

## Requested Mode
- Full end-to-end execution attempted against current M3 stack.
- All feature flags were set to `true` in scan start payload.
- Live-mode policy: no seeded/dummy fallback for primary scan.
- Program selection override active via `E2E_PINNED_PROGRAM_HANDLE` / `E2E_PINNED_PROGRAM_ID`.

## Execution Steps
1. 2026-03-24T00:07:46.261709+00:00 | Starting end-to-end system trace test
1. 2026-03-24T00:07:46.262008+00:00 | .env present (loaded 0 missing keys into process env)
1. 2026-03-24T00:07:47.548461+00:00 | Bringing up stack with docker compose up -d
1. 2026-03-24T00:07:52.499390+00:00 | Health probe scraper: status_code=200
1. 2026-03-24T00:07:52.976886+00:00 | Health probe core-engine: status_code=200
1. 2026-03-24T00:08:26.217743+00:00 | Health probe reporter: status_code=None
1. 2026-03-24T00:08:59.710301+00:00 | Health probe attack-graph-engine: status_code=None
1. 2026-03-24T00:09:00.364805+00:00 | Health probe api-gateway: status_code=200
1. 2026-03-24T00:09:01.541845+00:00 | Connected to database backend=docker-exec (core-engine) | PostgreSQL 16.13 (Debian 16.13-1.pgdg13+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
1. 2026-03-24T00:09:01.541868+00:00 | Pinned program selector configured: E2E_PINNED_PROGRAM_ID=None, E2E_PINNED_PROGRAM_HANDLE='weblate'
1. 2026-03-24T00:09:01.541871+00:00 | HackerOne credentials detected; triggering live scraper sync
1. 2026-03-24T00:13:02.036576+00:00 | Scraper trigger request failed; continuing with current live program inventory. error=ReadTimeout: 
1. 2026-03-24T00:13:24.525775+00:00 | Selected live HackerOne program for scan: 2715b22b-3506-4fb1-bece-95cad2eec341 (weblate) via policy=pinned_program_handle
1. 2026-03-24T00:13:25.788099+00:00 | Queue purge pre-check scan.jobs: ready=0 unacked=0 consumers=0
1. 2026-03-24T00:13:27.152878+00:00 | Queue purge attempt #1 scan.jobs: ok=True status=204 ready_before=0 ready_after=0
1. 2026-03-24T00:13:27.551614+00:00 | Queue purge settle window scan.jobs: settled_unacked=True ready=0 unacked=0
1. 2026-03-24T00:13:28.906470+00:00 | Queue purge attempt #2 scan.jobs: ok=True status=204 ready_before=0 ready_after=0
1. 2026-03-24T00:13:28.906507+00:00 | Waiting for queue baseline before triggering scan: queue=scan.jobs ready=0 timeout=60s
1. 2026-03-24T00:13:29.387371+00:00 | Queue baseline poll scan.jobs: ready=0 unacked=0 consumers=0
1. 2026-03-24T00:13:29.388613+00:00 | Queue baseline reached: scan.jobs ready=0
1. 2026-03-24T00:13:29.388622+00:00 | Triggering core scan with all feature flags enabled
1. 2026-03-24T00:13:40.447328+00:00 | Failure captured: Scan start failed with status=500: Internal Server Error

## Runtime Context
- DB connection backend: `docker-exec (core-engine) | PostgreSQL 16.13 (Debian 16.13-1.pgdg13+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit`
- Live HackerOne mode: `True`
- Program source: `hackerone_live_pinned`
- Program selection policy: `pinned_program_handle`
- Pinned program handle override: `weblate`
- Pinned program ID override: `None`
- Program ID: `2715b22b-3506-4fb1-bece-95cad2eec341`
- Program handle: `weblate`
- Scan ID: `None`
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
  "error": "ReadTimeout: ",
  "payload": null,
  "status_code": null
}
```

## Program Selection Audit
| program_id | handle | name | platform | is_active | valid_in_scope_count | selected | reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
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
| db9b007c-03ce-40ad-908e-3ea812e5968c | flipkart | Flipkart | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
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
| e6f0e835-e637-4954-8e75-a859fced1c55 | hilton | Hilton | hackerone | True | 17 | False | not selected: run pinned to explicit program selector(s) |
| cfcef7a2-26a9-43e3-a3a3-c7413b693dcd | allegion | Allegion | hackerone | True | 134 | False | not selected: run pinned to explicit program selector(s) |
| 1ff8cf28-980c-4186-9c32-1321b5bccf4d | wickr | Wickr | hackerone | True | 13 | False | not selected: run pinned to explicit program selector(s) |
| 81ee7cc0-102d-4383-8ac7-f296f6b04a9c | agoric | Agoric | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| e11db1c4-dcaa-45fc-b403-d83818783b09 | wellsfargo-bbp | Wells Fargo Bounty | hackerone | True | 14 | False | not selected: run pinned to explicit program selector(s) |
| 136f26e5-c9cb-40c0-8827-565f00b80883 | fresenius | Fresenius | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| eeffd5de-4f21-4a87-a06d-da929a1278af | amazonvrp-devices | Amazon Vulnerability Research Program - Devices | hackerone | True | 33 | False | not selected: run pinned to explicit program selector(s) |
| 518e040c-fb7c-45e0-a920-553eff264f5d | mondelez | Mondelēz International | hackerone | True | 311 | False | not selected: run pinned to explicit program selector(s) |
| 54f5a094-36b6-4876-bd22-137055d49cfe | palantir_public | Palantir Public | hackerone | True | 2 | False | not selected: run pinned to explicit program selector(s) |
| 2ca88bf3-1813-4c42-bad0-3137b31ae4b7 | divvy-homes | Divvy Homes | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 41088ada-d97b-4bcb-89eb-48838ebb963c | disney | The Walt Disney Company | hackerone | True | 17 | False | not selected: run pinned to explicit program selector(s) |
| 109dd66a-2651-4642-9682-3d83d55ca559 | inspectorio | Inspectorio | hackerone | True | 10 | False | not selected: run pinned to explicit program selector(s) |
| 579146b3-6fca-4a56-ba25-02e0b3546573 | clarivate | Clarivate | hackerone | True | 5027 | False | not selected: run pinned to explicit program selector(s) |
| a167fa9d-ef6e-42e7-b50a-eb1b285cdae0 | godaddy-vdp | GoDaddy VDP | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 75801c9c-22ca-403a-bb30-1261c36c3cf1 | veeam | Veeam | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| 588f2cf8-393f-4ed0-a335-636792279162 | moonpay | MoonPay  | hackerone | True | 14 | False | not selected: run pinned to explicit program selector(s) |
| 232c9f17-efc2-4617-9762-2b4e5d36f3f5 | redis-vdp | Redis VDP | hackerone | True | 5 | False | not selected: run pinned to explicit program selector(s) |
| b991b629-eaf0-4eca-9c07-a5aa3f567157 | pagerduty | PagerDuty | hackerone | True | 18 | False | not selected: run pinned to explicit program selector(s) |
| 5b465710-b91f-46be-b8e2-004972fd0262 | apnic | APNIC | hackerone | True | 18 | False | not selected: run pinned to explicit program selector(s) |
| af48f049-eb34-47b5-8d69-2a5166f6144b | blend-labs | Blend Labs | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| acd2f7fc-8475-40c0-8308-e9a8957d150b | caterpillar | Caterpillar | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 35c77130-6fde-4537-85a4-c3990ba43ffe | ibb | Internet Bug Bounty | hackerone | True | 21 | False | not selected: run pinned to explicit program selector(s) |
| 621d8179-be24-4b5f-978a-c8d31be34693 | razorpay | Razorpay | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| 820d9d25-4b34-4c44-bbb4-671df9825875 | oanda | OANDA | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| 5d2eed5f-ac79-49c2-a15d-3071f5b5e57d | planet-labs | Planet Labs | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| 10e79ab8-2e17-43a6-bfad-bd130628ac8b | tenable | Tenable | hackerone | True | 15 | False | not selected: run pinned to explicit program selector(s) |
| bd44874f-ff07-431d-97d0-71798251d234 | fastly-vdp | Fastly VDP | hackerone | True | 6 | False | not selected: run pinned to explicit program selector(s) |
| 92f115ef-2130-4a58-8857-a9e85201c512 | sega | SEGA | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| d601075b-ca6f-4609-a601-04d4a9bc708e | koho | KOHO | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| a902e3b1-214a-47f1-885a-0b199fdc97d6 | hy-vee | Hy-Vee | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 23309003-ba37-41c5-98b3-198026dd524b | octopus-energy | Octopus Energy Group | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| bc6dfc77-1b8c-4120-92be-19d4654db9d4 | newegg | Newegg | hackerone | True | 8 | False | not selected: run pinned to explicit program selector(s) |
| 7b6007b3-aaac-473e-92d1-1a58890e8079 | keurigdrpepper | Keurig Dr Pepper | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| c9494122-3510-4571-b606-57ae1ee75867 | tesco | Tesco | hackerone | True | 24 | False | not selected: run pinned to explicit program selector(s) |
| fafaf645-02f5-4e3a-ab61-6941bc59a751 | servicenow-disclosure | ServiceNow Disclosure | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| aac11905-f1eb-47d7-b724-2265d98be3f9 | particle-health-vdp | Particle Health VDP | hackerone | True | 9 | False | not selected: run pinned to explicit program selector(s) |
| 9e3aa617-101e-46b6-adb1-c0175cc6db0b | krisp | Krisp | hackerone | True | 15 | False | not selected: run pinned to explicit program selector(s) |
| 193d8103-e71a-404e-b43a-8a001a19084a | zooplus | Zooplus | hackerone | True | 4 | False | not selected: run pinned to explicit program selector(s) |
| f3d84e78-8bc1-49cf-b4c9-816deaf78644 | whatnot | Whatnot | hackerone | True | 7 | False | not selected: run pinned to explicit program selector(s) |
| d77d1b7e-7d32-4170-b750-7415e8ab102b | us-department-of-state | U.S. Department of State | hackerone | True | 24 | False | not selected: run pinned to explicit program selector(s) |
| afdf5c2d-194b-44c7-ab5e-eebf867ff67b | latamairlines | LATAM Airlines | hackerone | True | 28 | False | not selected: run pinned to explicit program selector(s) |
| 478ced79-94c0-45af-8b5b-793f3d3d1c8e | zurich-insurance | Zurich Insurance | hackerone | True | 42 | False | not selected: run pinned to explicit program selector(s) |
| 637948a7-7eaa-4b1e-a8fc-6ef18139f68c | nominet | Nominet | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| 9c0104c8-a0f9-4410-95c9-a42dbfac8871 | upchieve | UPchieve | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| d9b173c9-51bd-4719-8aba-2278cc755c2e | khealth | KHealth | hackerone | True | 24 | False | not selected: run pinned to explicit program selector(s) |
| a9df3ef4-e0e4-40e3-884a-fbcb354ce684 | smtp2go | SMTP2GO BBP | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |
| a425d59f-0bcb-43a4-beaa-9d38c85bea98 | playtika | Playtika | hackerone | True | 65 | False | not selected: run pinned to explicit program selector(s) |
| f879243f-0c72-47a6-b5c5-25fda3a7bada | beiersdorf | Beiersdorf | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| f147bc2f-f163-465a-bd11-c18954aaae18 | mcuboot | MCUboot | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 9744dd16-7b09-4bb7-9b46-116defd349c7 | vodafone | Vodafone | hackerone | True | 67 | False | not selected: run pinned to explicit program selector(s) |
| f58f5975-a765-4822-a95a-be2748493836 | fastify | Fastify | hackerone | True | 1 | False | not selected: run pinned to explicit program selector(s) |
| 1ddce056-d0a2-4218-9e42-5010f5a752f9 | trendyol | Trendyol | hackerone | True | 12 | False | not selected: run pinned to explicit program selector(s) |
| dd36fa14-14f7-4b74-aa3a-516429ca71d4 | compass-bbp | Compass | hackerone | True | 3 | False | not selected: run pinned to explicit program selector(s) |

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
  "payload": "Internal Server Error",
  "status_code": 500
}
```

### Final Scan Row
```json
{}
```

### Scan Wait Result
```json
{}
```

### Pipeline Stage Timeline
_None_

### Artifact Counts
```json
{}
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
{}
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
        "consumers": 0,
        "exists": true,
        "messages": 0,
        "messages_ready": 0,
        "messages_unacknowledged": 0,
        "queue": "scan.jobs",
        "status_code": 200
      },
      "state_before": {
        "consumers": 0,
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
        "consumers": 0,
        "exists": true,
        "messages": 0,
        "messages_ready": 0,
        "messages_unacknowledged": 0,
        "queue": "scan.jobs",
        "status_code": 200
      },
      "state_before": {
        "consumers": 0,
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
    "consumers": 0,
    "exists": true,
    "messages": 0,
    "messages_ready": 0,
    "messages_unacknowledged": 0,
    "queue": "scan.jobs",
    "status_code": 200
  },
  "initial_state": {
    "consumers": 0,
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
    "consumers": 0,
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
    "consumers": 0,
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
_None_

## API Snapshots
### /scans/{scan_id}
```json
{}
```

### /scans/{scan_id}/findings
```json
{}
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
 Container attackbot-prometheus-1 Running 
 Container attackbot-neo4j-1 Running 
 Container attackbot-redis-1 Running 
 Container attackbot-minio-1 Running 
 Container attackbot-loki-1 Running 
 Container attackbot-grafana-1 Running 
 Container attackbot-rabbitmq-1 Running 
 Container attackbot-postgres-1 Running 
 Container attackbot-vault-1 Running 
 Container attackbot-attack-graph-engine-1 Running 
 Container attackbot-core-engine-1 Running 
 Container attackbot-scraper-1 Running 
 Container attackbot-reporter-1 Running 
 Container attackbot-core-worker-1 Running 
 Container attackbot-api-gateway-1 Running 
 Container attackbot-tempo-1 Starting 
 Container attackbot-postgres-1 Waiting 
 Container attackbot-vault-1 Waiting 
 Container attackbot-minio-1 Waiting 
 Container attackbot-tempo-1 Started 
 Container attackbot-minio-1 Healthy 
 Container attackbot-minio-init-1 Starting 
 Container attackbot-postgres-1 Healthy 
 Container attackbot-migrate-1 Starting 
 Container attackbot-vault-1 Healthy 
 Container attackbot-vault-init-1 Starting 
 Container attackbot-minio-init-1 Started 
 Container attackbot-vault-init-1 Started 
 Container attackbot-migrate-1 Started 
 Container attackbot-redis-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-migrate-1 Waiting 
 Container attackbot-minio-init-1 Waiting 
 Container attackbot-postgres-1 Waiting 
 Container attackbot-minio-init-1 Waiting 
 Container attackbot-postgres-1 Waiting 
 Container attackbot-redis-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-migrate-1 Waiting 
 Container attackbot-migrate-1 Waiting 
 Container attackbot-neo4j-1 Waiting 
 Container attackbot-migrate-1 Waiting 
 Container attackbot-minio-init-1 Waiting 
 Container attackbot-postgres-1 Waiting 
 Container attackbot-redis-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-postgres-1 Healthy 
 Container attackbot-neo4j-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-minio-init-1 Exited 
 Container attackbot-postgres-1 Healthy 
 Container attackbot-redis-1 Healthy 
 Container attackbot-redis-1 Healthy 
 Container attackbot-minio-init-1 Exited 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-minio-init-1 Exited 
 Container attackbot-redis-1 Healthy 
 Container attackbot-postgres-1 Healthy 
 Container attackbot-migrate-1 Exited 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-migrate-1 Exited 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-redis-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-rabbitmq-1 Waiting 
 Container attackbot-migrate-1 Exited 
 Container attackbot-migrate-1 Exited 
 Container attackbot-scraper-1 Waiting 
 Container attackbot-core-engine-1 Waiting 
 Container attackbot-reporter-1 Waiting 
 Container attackbot-attack-graph-engine-1 Waiting 
 Container attackbot-reporter-1 Waiting 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-reporter-1 Healthy 
 Container attackbot-reporter-worker-1 Starting 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-ai-analysis-worker-1 Starting 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-api-fuzzer-worker-1 Starting 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-js-analysis-worker-1 Starting 
 Container attackbot-rabbitmq-1 Healthy 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-attack-graph-engine-1 Healthy 
 Container attackbot-exploit-verifier-1 Starting 
 Container attackbot-redis-1 Healthy 
 Container attackbot-browser-worker-1 Starting 
 Container attackbot-reporter-1 Healthy 
 Container attackbot-scraper-1 Healthy 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-scenario-runner-1 Starting 
 Container attackbot-core-engine-1 Healthy 
 Container attackbot-ai-analysis-worker-1 Started 
 Container attackbot-api-fuzzer-worker-1 Started 
 Container attackbot-js-analysis-worker-1 Started 
 Container attackbot-exploit-verifier-1 Started 
 Container attackbot-reporter-worker-1 Started 
 Container attackbot-scenario-runner-1 Started 
 Container attackbot-browser-worker-1 Started 

```

### Command: docker compose ps
- Return code: `0`
- Command: `docker compose -f C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1\infra\docker-compose.yml --env-file C:\Users\Haseeb\Desktop\Projects\Startup\Attackbot_v1\.env ps`

```text
STDOUT:
NAME                              IMAGE                           COMMAND                  SERVICE               CREATED          STATUS                                  PORTS
attackbot-ai-analysis-worker-1    attackbot-ai-analysis-worker    "celery -A backend.sâ€¦"   ai-analysis-worker    15 minutes ago   Restarting (1) 7 seconds ago            
attackbot-api-fuzzer-worker-1     attackbot-api-fuzzer-worker     "celery -A backend.sâ€¦"   api-fuzzer-worker     15 minutes ago   Restarting (1) 10 seconds ago           
attackbot-api-gateway-1           attackbot-api-gateway           "uvicorn backend.serâ€¦"   api-gateway           15 minutes ago   Up 12 minutes (unhealthy)               0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
attackbot-attack-graph-engine-1   attackbot-attack-graph-engine   "uvicorn backend.serâ€¦"   attack-graph-engine   15 minutes ago   Up 15 minutes (healthy)                 8006/tcp
attackbot-browser-worker-1        attackbot-browser-worker        "celery -A backend.sâ€¦"   browser-worker        15 minutes ago   Restarting (1) 5 seconds ago            
attackbot-core-engine-1           attackbot-core-engine           "uvicorn backend.serâ€¦"   core-engine           56 seconds ago   Up 49 seconds (healthy)                 0.0.0.0:8002->8002/tcp, [::]:8002->8002/tcp
attackbot-core-worker-1           attackbot-core-worker           "celery -A backend.sâ€¦"   core-worker           54 seconds ago   Up 16 seconds                           8002/tcp
attackbot-exploit-verifier-1      attackbot-exploit-verifier      "celery -A backend.sâ€¦"   exploit-verifier      15 minutes ago   Restarting (1) 8 seconds ago            
attackbot-grafana-1               grafana/grafana:latest          "/run.sh"                grafana               16 minutes ago   Up 15 minutes                           0.0.0.0:3000->3000/tcp, [::]:3000->3000/tcp
attackbot-js-analysis-worker-1    attackbot-js-analysis-worker    "celery -A backend.sâ€¦"   js-analysis-worker    15 minutes ago   Restarting (1) 8 seconds ago            
attackbot-loki-1                  grafana/loki:latest             "/usr/bin/loki -confâ€¦"   loki                  16 minutes ago   Up 15 minutes                           3100/tcp
attackbot-minio-1                 minio/minio                     "/usr/bin/docker-entâ€¦"   minio                 16 minutes ago   Up 15 minutes (healthy)                 9000/tcp
attackbot-neo4j-1                 neo4j:5-community               "tini -g -- /startupâ€¦"   neo4j                 16 minutes ago   Up 15 minutes (healthy)                 7473-7474/tcp, 7687/tcp
attackbot-postgres-1              postgres:16                     "docker-entrypoint.sâ€¦"   postgres              16 minutes ago   Up 15 minutes (healthy)                 0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp
attackbot-prometheus-1            prom/prometheus:latest          "/bin/prometheus --câ€¦"   prometheus            16 minutes ago   Up 15 minutes                           9090/tcp
attackbot-rabbitmq-1              rabbitmq:3-management           "docker-entrypoint.sâ€¦"   rabbitmq              16 minutes ago   Up 16 minutes (healthy)                 0.0.0.0:15672->15672/tcp, [::]:15672->15672/tcp
attackbot-redis-1                 redis:7-alpine                  "docker-entrypoint.sâ€¦"   redis                 16 minutes ago   Up 15 minutes (healthy)                 6379/tcp
attackbot-reporter-1              attackbot-reporter              "uvicorn backend.serâ€¦"   reporter              15 minutes ago   Up 15 minutes (healthy)                 8003/tcp
attackbot-reporter-worker-1       attackbot-reporter-worker       "celery -A backend.sâ€¦"   reporter-worker       15 minutes ago   Restarting (1) 44 seconds ago           
attackbot-scenario-runner-1       attackbot-scenario-runner       "celery -A backend.sâ€¦"   scenario-runner       15 minutes ago   Restarting (1) 6 seconds ago            
attackbot-scraper-1               attackbot-scraper               "uvicorn backend.serâ€¦"   scraper               56 seconds ago   Up 49 seconds (healthy)                 0.0.0.0:8001->8001/tcp, [::]:8001->8001/tcp
attackbot-tempo-1                 grafana/tempo:latest            "/tempo"                 tempo                 16 minutes ago   Restarting (1) Less than a second ago   
attackbot-vault-1                 hashicorp/vault:1.15            "docker-entrypoint.sâ€¦"   vault                 16 minutes ago   Up 15 minutes (healthy)                 8200/tcp


STDERR:
<empty>
```

## Observed Gaps in Current Implementation
- Reporter worker currently validates `report.jobs` envelopes only.
- Specialist workers are queue listeners; deeper stages land in later milestones.
- This report reflects what ran in this test session, not aspirational docs.
