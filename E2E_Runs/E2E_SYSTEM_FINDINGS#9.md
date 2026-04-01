# AttackBot End-to-End Findings Report

- Generated at: `2026-03-25T13:04:38.149327+00:00`
- Report file: `E2E_Runs/E2E_SYSTEM_FINDINGS#9.md`
- Project root: `C:\Users\Home\Desktop\Projects\Attackbot_v1`
- Test outcome: `completed`

## Requested Mode
- Full end-to-end execution attempted against current M3 stack.
- All feature flags were set to `true` in scan start payload.
- Live-mode policy: no seeded/dummy fallback for primary scan.
- Known vulnerable target mode active via `E2E_KNOWN_VULN_TARGET_URL`.

## Execution Steps
1. 2026-03-25T13:01:54.683665+00:00 | Starting end-to-end system trace test
1. 2026-03-25T13:01:54.684097+00:00 | .env present (loaded 0 missing keys into process env)
1. 2026-03-25T13:01:55.125014+00:00 | Bringing up stack with docker compose up -d
1. 2026-03-25T13:02:01.049571+00:00 | Health probe scraper: status_code=200
1. 2026-03-25T13:02:01.874139+00:00 | Health probe core-engine: status_code=200
1. 2026-03-25T13:02:32.012558+00:00 | Health probe reporter: status_code=None
1. 2026-03-25T13:03:06.622420+00:00 | Health probe attack-graph-engine: status_code=None
1. 2026-03-25T13:03:07.538610+00:00 | Health probe api-gateway: status_code=200
1. 2026-03-25T13:03:09.577415+00:00 | Connected to database backend=docker-exec (core-engine) | PostgreSQL 16.13 (Debian 16.13-1.pgdg13+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
1. 2026-03-25T13:03:09.577488+00:00 | Known vulnerable target mode configured: E2E_KNOWN_VULN_TARGET_URL='http://host.docker.internal:3001' E2E_KNOWN_VULN_PROGRAM_HANDLE='known-vuln-target'
1. 2026-03-25T13:03:09.577505+00:00 | Known vulnerable target mode active; skipping live scraper sync trigger
1. 2026-03-25T13:03:16.713673+00:00 | Upserted known vulnerable target program: program_id=82f21365-d27c-5352-a67f-af2eb0fddc8a handle=known-vuln-target
1. 2026-03-25T13:03:18.305157+00:00 | Selected known vulnerable target program for scan: 82f21365-d27c-5352-a67f-af2eb0fddc8a (known-vuln-target) target_url=http://host.docker.internal:3001
1. 2026-03-25T13:03:22.068579+00:00 | Queue purge pre-check scan.jobs: ready=0 unacked=0 consumers=1
1. 2026-03-25T13:03:23.745140+00:00 | Queue purge attempt #1 scan.jobs: ok=True status=204 ready_before=0 ready_after=0
1. 2026-03-25T13:03:24.297979+00:00 | Queue purge settle window scan.jobs: settled_unacked=True ready=0 unacked=0
1. 2026-03-25T13:03:25.981911+00:00 | Queue purge attempt #2 scan.jobs: ok=True status=204 ready_before=0 ready_after=0
1. 2026-03-25T13:03:25.981933+00:00 | Waiting for queue baseline before triggering scan: queue=scan.jobs ready=0 unacked=0 timeout=60s
1. 2026-03-25T13:03:26.508573+00:00 | Queue baseline poll scan.jobs: ready=0 unacked=0 consumers=1
1. 2026-03-25T13:03:26.508603+00:00 | Queue baseline reached: scan.jobs ready=0 unacked=0
1. 2026-03-25T13:03:26.508609+00:00 | Triggering core scan with all feature flags enabled
1. 2026-03-25T13:03:49.048351+00:00 | Scan status transition observed: running
1. 2026-03-25T13:04:25.117576+00:00 | Scan status transition observed: completed
1. 2026-03-25T13:04:25.117609+00:00 | Terminal scan status reached: completed

## Runtime Context
- DB connection backend: `docker-exec (core-engine) | PostgreSQL 16.13 (Debian 16.13-1.pgdg13+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit`
- Live HackerOne mode: `False`
- Program source: `known_vuln_target_seeded`
- Program selection policy: `known_vuln_target_url`
- Pinned program handle override: `None`
- Pinned program ID override: `None`
- Known vulnerable target URL override: `http://host.docker.internal:3001`
- Known vulnerable target handle override: `known-vuln-target`
- Program ID: `82f21365-d27c-5352-a67f-af2eb0fddc8a`
- Program handle: `known-vuln-target`
- Scan ID: `a3c9c33f-60e4-44fc-a95e-51eaee0542dd`
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
{}
```

## Program Selection Audit
| program_id | handle | name | platform | is_active | valid_in_scope_count | selected | reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 82f21365-d27c-5352-a67f-af2eb0fddc8a | known-vuln-target | Known Vulnerable Target | hackerone | True | 2 | True | selected: known vulnerable target mode (E2E_KNOWN_VULN_TARGET_URL=http://host.docker.internal:3001) |
| 965264b1-72b3-4440-b6e3-1ccc94a94ee5 | costco | Costco | hackerone | True | 14 | False | not selected: single-program live e2e chooses most recent eligible program |
| 27a683d6-b735-43a5-9f21-b31560b6e6bc | paystack-vdp | Paystack Vulnerability Disclosure | hackerone | True | 14 | False | not selected: single-program live e2e chooses most recent eligible program |
| 17207810-4029-404f-b8d9-2da539dbd79d | stripe | Stripe | hackerone | True | 46 | False | not selected: single-program live e2e chooses most recent eligible program |
| ea461be5-35f5-4ecc-ab2e-d573dd19ce26 | on | On  | hackerone | True | 5 | False | not selected: single-program live e2e chooses most recent eligible program |
| c2feb45b-eacb-4955-a6b4-a5ec80ccc5f5 | judgeme | Judge.me  | hackerone | True | 6 | False | not selected: single-program live e2e chooses most recent eligible program |
| f2119d6d-fb74-46b9-9419-45302bf343d0 | doppler | Doppler | hackerone | True | 6 | False | not selected: single-program live e2e chooses most recent eligible program |
| 8224b951-a14e-4e2c-b546-0bb04e09b35a | gymshark | Gymshark | hackerone | True | 6 | False | not selected: single-program live e2e chooses most recent eligible program |
| 43025e89-f94b-416f-bea7-5dd4d7b327e3 | emoney-advisor | eMoney Advisor | hackerone | True | 3 | False | not selected: single-program live e2e chooses most recent eligible program |
| 918c5259-00c9-4cdc-aebb-fa5f0546deb5 | grindr | Grindr | hackerone | True | 9 | False | not selected: single-program live e2e chooses most recent eligible program |
| 750c96db-7d4d-45a7-bd83-f62429b56256 | csg-public | Cloud Software Group | hackerone | True | 17 | False | not selected: single-program live e2e chooses most recent eligible program |
| 2d65c54f-7a28-4819-a50f-37c4b87088a9 | gsa_bbp | GSA Bounty | hackerone | True | 46 | False | not selected: single-program live e2e chooses most recent eligible program |
| 4b9e6bb3-6b40-49b8-b275-551759f357f5 | mars | Mars | hackerone | True | 110 | False | not selected: single-program live e2e chooses most recent eligible program |
| 1d8c34fa-014b-4979-b543-20bd3ccbf928 | gsa_vdp | U.S. General Services Administration | hackerone | True | 426 | False | not selected: single-program live e2e chooses most recent eligible program |
| ed3fdbb7-c7ef-4275-bff3-6d71b7d3af95 | xvideos | XVIDEOS | hackerone | True | 5 | False | not selected: single-program live e2e chooses most recent eligible program |
| 7282ad2a-eb46-4cff-a0a4-4d8732d8c947 | trafficfactory | Traffic Factory | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 0f7e5b3b-61da-4f37-b4a3-b789d0b6c0ea | anywhererealestate | Anywhere Real Estate | hackerone | True | 16 | False | not selected: single-program live e2e chooses most recent eligible program |
| 65dfaee9-6e98-4313-9a2d-780c15be491b | ohiosecretaryofstate | Ohio Secretary of State | hackerone | True | 10 | False | not selected: single-program live e2e chooses most recent eligible program |
| c5db3186-e2c0-4d96-85a9-dd10fdea04d4 | freshworks | Freshworks  | hackerone | True | 17 | False | not selected: single-program live e2e chooses most recent eligible program |
| 70466828-60b4-40db-87de-ca6555757334 | wonder-vdp | Blue Apron (Wonder Group) VDP | hackerone | True | 25 | False | not selected: single-program live e2e chooses most recent eligible program |
| 289612cc-feef-40f6-8858-bb280f778af5 | cbre | CBRE | hackerone | True | 8716 | False | not selected: single-program live e2e chooses most recent eligible program |
| 6cd0df80-79ad-4b9b-b3c0-88d32b63d0c8 | hudapp | Hud App | hackerone | True | 8 | False | not selected: single-program live e2e chooses most recent eligible program |
| 0fe1ff39-0a6b-4b8d-9928-f526c2bca3b4 | 8x8-bounty | 8x8 | hackerone | True | 99 | False | not selected: single-program live e2e chooses most recent eligible program |
| 5b4d8cdf-ff00-49d7-9fd6-3b6a7ad5698b | john-deere | John Deere | hackerone | True | 1909 | False | not selected: single-program live e2e chooses most recent eligible program |
| 710858d8-30f4-4e0b-bf63-24e0bb228afb | tiktok | TikTok | hackerone | True | 39 | False | not selected: single-program live e2e chooses most recent eligible program |
| 1315fda6-c093-4389-9365-24d464660591 | dropcontact | Dropcontact | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| 92b67def-d6cd-4210-90c7-6a6a5d6049d2 | aig | AIG | hackerone | True | 19 | False | not selected: single-program live e2e chooses most recent eligible program |
| 5a2a0bac-faec-431b-a3b2-1720a875eaeb | rebellion-defense | Rebellion Defense | hackerone | True | 6 | False | not selected: single-program live e2e chooses most recent eligible program |
| ce225b05-de93-4794-803a-68456b94b5bf | estee-lauder |  Esteé  Lauder | hackerone | True | 471 | False | not selected: single-program live e2e chooses most recent eligible program |
| 322b5053-7f3e-40a9-95b8-ce44c8056c90 | callsign | Callsign | hackerone | True | 5 | False | not selected: single-program live e2e chooses most recent eligible program |
| 63277526-d224-4d8f-9e43-18b402cfb2cd | polygon-technology | Polygon Technology | hackerone | True | 8 | False | not selected: single-program live e2e chooses most recent eligible program |
| d93974c0-de5d-4e92-9141-97fe3ea918c6 | finra | FINRA Response | hackerone | True | 2 | False | not selected: single-program live e2e chooses most recent eligible program |
| b8ecb6b7-4e68-43e7-adee-05a48b295d35 | blackrock | BlackRock | hackerone | True | 4 | False | not selected: single-program live e2e chooses most recent eligible program |
| 7ddb4bf8-e9f7-4d9f-94ce-0b90b67e508e | zebra_vdp | Zebra VDP | hackerone | True | 57 | False | not selected: single-program live e2e chooses most recent eligible program |
| c6b0154b-ef80-49ef-bb8f-f771e5093603 | launchdarkly | LaunchDarkly | hackerone | True | 6 | False | not selected: single-program live e2e chooses most recent eligible program |
| bb9eb57a-63c4-43fe-b6ec-fd0e74d15e5c | figma | Figma | hackerone | True | 7 | False | not selected: single-program live e2e chooses most recent eligible program |
| a015ce0e-3758-472b-9b2b-dd92fd149baa | vendasta | Vendasta | hackerone | True | 11 | False | not selected: single-program live e2e chooses most recent eligible program |
| e392fb6a-f758-40b9-bf1c-c9dc3873b3e1 | cs_money | CS Money | hackerone | True | 5 | False | not selected: single-program live e2e chooses most recent eligible program |
| 9a9f66f7-894d-4166-8b8d-7dd63783218d | mendix | Mendix | hackerone | True | 23 | False | not selected: single-program live e2e chooses most recent eligible program |
| b67cfba5-4d87-4696-80a7-4fe58039fb72 | lichess | Lichess | hackerone | True | 48 | False | not selected: single-program live e2e chooses most recent eligible program |
| 696b5925-0209-422e-a6d6-e946391d7f3f | trycourier | Courier | hackerone | True | 5 | False | not selected: single-program live e2e chooses most recent eligible program |
| 4f937622-125c-4983-b12d-e561d0ea3ebc | shutterfly_vdp | Shutterfly VDP | hackerone | True | 35 | False | not selected: single-program live e2e chooses most recent eligible program |
| cb6ddb1d-7b2f-4133-befd-d9e1d1e3f559 | n45ht | N45HT | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| 2873891f-c2e9-4b1a-8e3e-936397c26fd1 | h1-ctf | h1-ctf | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| 26fa2031-3729-4468-9d60-0fa822495417 | cognizant | Cognizant | hackerone | True | 26 | False | not selected: single-program live e2e chooses most recent eligible program |
| 3ccf26f1-1c29-4ecb-80f0-4bad95f982c9 | ups | UPS VDP | hackerone | True | 3 | False | not selected: single-program live e2e chooses most recent eligible program |
| 6fabb9ea-a090-43d9-8018-88ca2b430389 | alibaba | Alibaba BBP | hackerone | True | 13 | False | not selected: single-program live e2e chooses most recent eligible program |
| 86514cb2-9ee7-4045-b700-23068381f6fb | openmage | OpenMage | hackerone | True | 3 | False | not selected: single-program live e2e chooses most recent eligible program |
| 803dcf50-c57c-484c-9ba9-c9c65d6b5c0e | shein | SHEIN | hackerone | True | 7 | False | not selected: single-program live e2e chooses most recent eligible program |
| 42bff9f7-a981-4dd6-a573-740a4ddc4afb | logsnitch | LogSnitch | hackerone | True | 8 | False | not selected: single-program live e2e chooses most recent eligible program |
| 8ba91bf7-af2b-41df-b14f-efefd02fb258 | cedars-sinai | Cedars-Sinai | hackerone | True | 39 | False | not selected: single-program live e2e chooses most recent eligible program |
| f835eb2d-7557-41ec-b92f-bf39a884816c | flexport_vdp | Flexport VDP | hackerone | True | 2 | False | not selected: single-program live e2e chooses most recent eligible program |
| be220f3d-88ef-4400-8c60-49b49a16855d | gener8 | Gener8 | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| 5b120193-97b0-4c7f-800b-219afa4cf6b7 | cirrusinsight | Cirrus Insight | hackerone | True | 2 | False | not selected: single-program live e2e chooses most recent eligible program |
| 2fe4446d-5174-47e3-8a51-2b0d2d7f1165 | stagingdoteverydotorg | Staging.every.org | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| 5543a319-be5e-4883-8126-93f4d34237c2 | navient_solutions | Navient Solutions LLC | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| 771c2f24-ca9f-4bb2-8ded-a7fe986e44d5 | btfs | BTFS | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 81110ddb-3a2d-4d5c-9415-7078af80f806 | r3 | R3 | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| 97effe20-2938-4b3a-b93a-6a60db824426 | faraday_inc | Faraday, Inc. | hackerone | True | 7 | False | not selected: single-program live e2e chooses most recent eligible program |
| d9821596-5413-4c83-91bc-7a5346ed5b75 | td-bank | TD Bank Group | hackerone | True | 20 | False | not selected: single-program live e2e chooses most recent eligible program |
| 12eb7baf-9ac4-4138-9392-060767197fa5 | aiven_ltd | Aiven Ltd | hackerone | True | 18 | False | not selected: single-program live e2e chooses most recent eligible program |
| f2f4243b-7709-4603-9fbc-2b5621588cd5 | hostinger | hostinger  | hackerone | True | 9 | False | not selected: single-program live e2e chooses most recent eligible program |
| 8ad84356-ab78-4607-b1d1-35c4f536b31c | standard_notes | Standard Notes | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 634b23d0-0361-4adf-bcd1-9d4e4a129c49 | simple_poll | Simple Poll | hackerone | True | 4 | False | not selected: single-program live e2e chooses most recent eligible program |
| 41dbef41-e07d-4980-b2dc-d74bc4c2aff2 | skale_network | SKALE Network | hackerone | True | 4 | False | not selected: single-program live e2e chooses most recent eligible program |
| cce5742d-76c7-485b-9be7-09722c5bc842 | rghost | RGhost | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| 3abb2f59-4f25-482e-93a5-b5632a6862f2 | playstation | PlayStation | hackerone | True | 18 | False | not selected: single-program live e2e chooses most recent eligible program |
| bdd062b4-d522-49a2-9891-e5883a270031 | myndr | Myndr | hackerone | True | 3 | False | not selected: single-program live e2e chooses most recent eligible program |
| 2309c43a-8d02-49fc-95d3-0eb9eeb2959e | pubg | PUBG | hackerone | True | 2 | False | not selected: single-program live e2e chooses most recent eligible program |
| 5fccff2b-e504-45f0-b88c-160e6dc69fec | chorus_jg4l2 | Chorus | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 4a0bba8e-8a12-4487-ac9f-cd832a487c2c | evernote | Evernote | hackerone | True | 9 | False | not selected: single-program live e2e chooses most recent eligible program |
| 00d87f92-f683-4e2e-aedc-b1366c1301d0 | earny | Earny | hackerone | True | 5 | False | not selected: single-program live e2e chooses most recent eligible program |
| 3b0dbe8f-12c2-4544-8eb6-f1122e9f7532 | usps | USPS - United States Postal Service | hackerone | True | 17 | False | not selected: single-program live e2e chooses most recent eligible program |
| 772b7f0a-2eab-44d8-843e-c53e6e20bbac | truecaller | Truecaller  | hackerone | True | 9 | False | not selected: single-program live e2e chooses most recent eligible program |
| c48e7bbd-a946-4240-aa30-d30f5ef5eb35 | picsart | Picsart | hackerone | True | 18 | False | not selected: single-program live e2e chooses most recent eligible program |
| 115116c9-7821-44d5-8f31-8aaebe2e8f43 | lemlist | lemlist | hackerone | True | 5 | False | not selected: single-program live e2e chooses most recent eligible program |
| 39ddc3c8-2235-488f-b526-5450ff7ba5ef | amazonvrp | Amazon Vulnerability Research Program | hackerone | True | 100 | False | not selected: single-program live e2e chooses most recent eligible program |
| 54f2e8cf-1aa9-42e3-a8f5-6b24ddb46d42 | hcl_software | HCL Software Inc. | hackerone | True | 48 | False | not selected: single-program live e2e chooses most recent eligible program |
| bccd1892-c449-4144-9ac1-fd7777535c04 | thomsonreuters-public | Thomson Reuters | hackerone | True | 2 | False | not selected: single-program live e2e chooses most recent eligible program |
| d92cab14-409c-4e69-ad48-29d7e6bfa9a4 | exodus | Exodus | hackerone | True | 11 | False | not selected: single-program live e2e chooses most recent eligible program |
| a77de624-2a02-4bd0-9cf5-21719c8179f2 | companyhub | CompanyHub | hackerone | True | 3 | False | not selected: single-program live e2e chooses most recent eligible program |
| d2b31872-c476-496f-9faa-933e35acb349 | gmelius | Gmelius | hackerone | True | 3 | False | not selected: single-program live e2e chooses most recent eligible program |
| 3e0ea45b-16b5-43ce-8fcf-e6051dac70e8 | mobisystems_ltd | MobiSystems Ltd. | hackerone | True | 4 | False | not selected: single-program live e2e chooses most recent eligible program |
| c5afde2a-fa7e-43b2-a4c7-99ed2d7cfe1d | thnks | Thnks | hackerone | True | 4 | False | not selected: single-program live e2e chooses most recent eligible program |
| c9e1a9cb-494c-4da9-bb1b-2e7f84371dfa | oasisprotocol | Oasis Protocol Foundation | hackerone | True | 13 | False | not selected: single-program live e2e chooses most recent eligible program |
| 25b995eb-8a71-424c-9508-98191cd9b8bd | copper | Copper | hackerone | True | 2 | False | not selected: single-program live e2e chooses most recent eligible program |
| e291283a-bece-4611-ad50-8cf947f576d8 | jnj_mobile | JNJ Mobile | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| 640526e0-fe25-42c8-9e75-317087ba78f0 | overloop | Overloop | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| 4056ed22-d013-4494-8aa1-291d9312b1ad | stripo | Stripo Inc | hackerone | True | 2 | False | not selected: single-program live e2e chooses most recent eligible program |
| 4976af33-8feb-4927-8400-893165527052 | palo_alto_software | Palo Alto Software | hackerone | True | 4 | False | not selected: single-program live e2e chooses most recent eligible program |
| 6778fdcb-f3c0-490d-8e4c-ed3b68b1cc7b | uphabit | UpHabit | hackerone | True | 4 | False | not selected: single-program live e2e chooses most recent eligible program |
| 317d2a46-3634-4a12-b07a-e19903883c0a | investnext | InvestNext | hackerone | True | 4 | False | not selected: single-program live e2e chooses most recent eligible program |
| 823e82ef-a3cb-4489-9704-a51c8915c67d | mtn_group | MTN Group | hackerone | True | 494 | False | not selected: single-program live e2e chooses most recent eligible program |
| 1c62e816-1266-4bc6-b029-4404d2588c53 | panther_labs | Panther Labs | hackerone | True | 3 | False | not selected: single-program live e2e chooses most recent eligible program |
| be13bad7-4386-41ed-98b9-7411b9af9bea | coinspot | CoinSpot | hackerone | True | 4 | False | not selected: single-program live e2e chooses most recent eligible program |
| 6366fb04-6e56-4b2d-a4ad-33622f339c55 | nuri | Nuri | hackerone | True | 8 | False | not selected: single-program live e2e chooses most recent eligible program |
| 9422141b-6275-475e-b821-2c01c6787b00 | people_interactive | People Interactive | hackerone | True | 2 | False | not selected: single-program live e2e chooses most recent eligible program |
| 3bab9a92-27de-4957-b41f-0bdb035237af | top_echelon_software | Top Echelon Software | hackerone | True | 3 | False | not selected: single-program live e2e chooses most recent eligible program |
| b4d07c09-ead0-4a6c-a2e3-1f83d6a347e2 | keybank | KeyBank | hackerone | True | 19 | False | not selected: single-program live e2e chooses most recent eligible program |
| b6792cbc-89a0-477d-888c-11640caac6d4 | aodocs | AODocs | hackerone | True | 2 | False | not selected: single-program live e2e chooses most recent eligible program |
| 26394514-3922-4dad-9cca-c8c291f5f6ce | solidus | Solidus | hackerone | True | 2 | False | not selected: single-program live e2e chooses most recent eligible program |
| 0ee323c9-6e84-4ece-a496-121e92fac183 | lark_technologies | Lark Technologies | hackerone | True | 18 | False | not selected: single-program live e2e chooses most recent eligible program |
| e6ab4892-aeca-4e40-979e-090e1dda18d5 | amitree_inc | Amitree Inc | hackerone | True | 2 | False | not selected: single-program live e2e chooses most recent eligible program |
| f9235c88-4efe-47e2-bd40-81acecf08e13 | worklytics | Worklytics | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| 2ac2b205-74d5-4aca-ac7c-030272f7893e | mailtime_technology_inc | Mailtime Technology Inc. | hackerone | True | 2 | False | not selected: single-program live e2e chooses most recent eligible program |
| 95741101-7103-4ae2-bd72-e4d65aa3138c | replyify | Replyify | hackerone | True | 5 | False | not selected: single-program live e2e chooses most recent eligible program |
| 41b60cd7-e6f0-44ec-834c-4bb520aa5a16 | raivo | Raivo | hackerone | True | 7 | False | not selected: single-program live e2e chooses most recent eligible program |
| ce1b6a76-0eef-4ba2-b2de-bc28eaddcb55 | consensys | Consensys | hackerone | True | 3 | False | not selected: single-program live e2e chooses most recent eligible program |
| beebec81-9337-4aa0-a7fa-c1ffdffd2991 | gocardless_bbp | GoCardless Bug Bounty Program | hackerone | True | 17 | False | not selected: single-program live e2e chooses most recent eligible program |
| 1e71635f-488b-43fc-b715-15065857f988 | dynatrace | Dynatrace | hackerone | True | 11 | False | not selected: single-program live e2e chooses most recent eligible program |
| ccec96ab-3727-49f6-8e23-07a5e32c6cf4 | forescout_technologies | ForeScout Technologies | hackerone | True | 63 | False | not selected: single-program live e2e chooses most recent eligible program |
| ce3d38f5-fc2a-40fd-b502-725b1386334d | kubernetes | Kubernetes | hackerone | True | 83 | False | not selected: single-program live e2e chooses most recent eligible program |
| c1e9c03d-7085-40fa-ab8d-d3d97637a0bb | midpoint_h1c | Midpoint (European Commission - DIGIT) | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| d4ff35d1-20b1-437f-ad5d-0a88e1e879b2 | impresscms | ImpressCMS | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| 9ac7e70a-7b20-44a5-b2b9-619e2b7b6c62 | starling_bank | Starling Bank VDP | hackerone | True | 12 | False | not selected: single-program live e2e chooses most recent eligible program |
| 8e306685-7aed-4c31-832b-c3c5f75cdab1 | spell | Spell | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| 2151cb2c-83a8-4709-b19d-b8bf1a34ff2b | endless_group | Endless Group | hackerone | True | 7 | False | not selected: single-program live e2e chooses most recent eligible program |
| 582ba165-340c-462e-8e88-2fdd8aa70af6 | early_warning | Early Warning | hackerone | True | 8 | False | not selected: single-program live e2e chooses most recent eligible program |
| ea28eb14-43ff-4f54-910f-517c4c877229 | ridewithvia | Via | hackerone | True | 13 | False | not selected: single-program live e2e chooses most recent eligible program |
| 311b3ec1-e862-4678-95af-09642bfd568b | apache_kafka_h1c | Apache Kafka (European Commission - DIGIT) | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| b81f2c67-a43b-45e6-a8ef-19f85147dbc1 | filezilla_h1c | FileZilla (European Commission - DIGIT) | hackerone | True | 3 | False | not selected: single-program live e2e chooses most recent eligible program |
| 0da5c421-5eb3-4917-88d0-acec7cd08682 | putty_h1c | PuTTY (European Commission - DIGIT) | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| 9d2fbc16-75b1-4fd5-bd65-2e7be64774dc | vlc_h1c | VLC (European Commission - DIGIT) | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| fdc4bd36-5ccb-4062-bddc-d17dce74f243 | filezilla | FileZilla | hackerone | True | 5 | False | not selected: single-program live e2e chooses most recent eligible program |
| 1af0200a-b789-47ca-bc0c-0ada7ea954e6 | capital-one | Capital One | hackerone | True | 27 | False | not selected: single-program live e2e chooses most recent eligible program |
| a71e9f2e-2f90-4ec0-b2f6-81ebba878727 | ford | Ford | hackerone | True | 27 | False | not selected: single-program live e2e chooses most recent eligible program |
| e7c1445e-3b87-4d52-a146-8fd2cf1f7e88 | reddit | Reddit | hackerone | True | 28 | False | not selected: single-program live e2e chooses most recent eligible program |
| cd6f7da3-10fc-48bd-a02c-bb0fe7d72962 | curl | curl | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| 68085551-a6f1-4995-8c11-437410b0e67e | remitano | Remitano | hackerone | True | 5 | False | not selected: single-program live e2e chooses most recent eligible program |
| e2fff78a-ecf4-4d6e-971d-b803b6a024a3 | instacart | Instacart | hackerone | True | 10 | False | not selected: single-program live e2e chooses most recent eligible program |
| 405fc1b8-752e-4b9c-acfe-07ae2ee2bafe | central-security-project | Central Security Project | hackerone | True | 3 | False | not selected: single-program live e2e chooses most recent eligible program |
| cbd10c54-be1a-4509-8f5c-ea0d27f170fb | fronthq | Front | hackerone | True | 6 | False | not selected: single-program live e2e chooses most recent eligible program |
| 41a1e9f5-81ef-4db4-b9e2-f3371ed6d34d | etoro_bbp | eToro BBP | hackerone | True | 42 | False | not selected: single-program live e2e chooses most recent eligible program |
| e33d02e7-2157-4b7e-a977-4498a2a73d77 | insulet_corporation | Insulet Corporation | hackerone | True | 19 | False | not selected: single-program live e2e chooses most recent eligible program |
| d881a921-c30c-484e-9531-99cdf8087e88 | fanduel | FanDuel | hackerone | True | 20 | False | not selected: single-program live e2e chooses most recent eligible program |
| 1c73fa85-6945-46e1-a6fc-b9bc8f570602 | sweatco_ltd | Sweatco Ltd | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| 20a0e8f6-e13e-4403-a1bc-d5db01c1eab5 | expediagroup_bbp | Expedia Group Bug Bounty | hackerone | True | 53 | False | not selected: single-program live e2e chooses most recent eligible program |
| 32e2fb94-54b4-413a-8857-61d180ad6b61 | urbancompany | Urban Company | hackerone | True | 6 | False | not selected: single-program live e2e chooses most recent eligible program |
| 2db2ffca-a15e-48a7-97a5-f48da6bfdf74 | creditkarma | Credit Karma | hackerone | True | 14 | False | not selected: single-program live e2e chooses most recent eligible program |
| 955a7cd5-4d7a-456c-905c-30bd156910a3 | mercadolibre | MercadoLibre | hackerone | True | 67 | False | not selected: single-program live e2e chooses most recent eligible program |
| 7c225209-349a-4fba-87be-346f58d5cefb | expediagroup | Expedia Group VDP | hackerone | True | 35 | False | not selected: single-program live e2e chooses most recent eligible program |
| 41ae4fe4-0e68-482e-9a82-cd2f17e5c567 | defectdojo | DefectDojo | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| 83f3858a-f1f7-41e3-8f56-ee8abca85fbc | flickr | Flickr | hackerone | True | 5 | False | not selected: single-program live e2e chooses most recent eligible program |
| 7e8813c0-4b39-4615-969e-9ecf26404bad | logitech | Logitech | hackerone | True | 86 | False | not selected: single-program live e2e chooses most recent eligible program |
| 15d9b87c-4022-442b-b0b8-d74811515508 | remitly | Remitly | hackerone | True | 26 | False | not selected: single-program live e2e chooses most recent eligible program |
| 135c6e67-72b1-4421-81fc-f83ff88a5dea | eslint | ESLint | hackerone | True | 3 | False | not selected: single-program live e2e chooses most recent eligible program |
| 995f1f36-42ad-47a6-ac49-1fcb58b0bc95 | chainlink | Chainlink | hackerone | True | 8 | False | not selected: single-program live e2e chooses most recent eligible program |
| a586b917-634b-4c80-9e03-49edb66caca3 | nisc | NISC-VDP | hackerone | True | 11 | False | not selected: single-program live e2e chooses most recent eligible program |
| eb057109-8ced-44b1-b573-5d717fa141b7 | marriott | Marriott Bug Bounty Program | hackerone | True | 80 | False | not selected: single-program live e2e chooses most recent eligible program |
| e4d1112d-cbdc-465a-9f68-c45c156d8ded | cfptime | CFP Time | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| 6848701b-69ee-4fd7-8490-8e3bd8364c80 | chaturbate | Chaturbate | hackerone | True | 9 | False | not selected: single-program live e2e chooses most recent eligible program |
| b5ac8061-4400-4252-abfe-f69ec6b6d541 | hannob | Hanno's projects | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| ff05b5b8-18ca-42a3-b232-c9edd6ea805c | s-pankki | S-Pankki | hackerone | True | 14 | False | not selected: single-program live e2e chooses most recent eligible program |
| e05cfe25-b802-4f2d-bd5c-df7339dae5da | arkadiyt-projects | arkadiyt-projects | hackerone | True | 8 | False | not selected: single-program live e2e chooses most recent eligible program |
| 1881f6ca-9b8f-4df0-b575-034c37a6a06d | pixiv | pixiv | hackerone | True | 17 | False | not selected: single-program live e2e chooses most recent eligible program |
| 2aab1a9c-5176-4da8-acea-6cc322bc0c10 | liberapay | Liberapay | hackerone | True | 3 | False | not selected: single-program live e2e chooses most recent eligible program |
| 167c9df5-c7e3-4561-a711-0d0282adbced | crypto | Crypto.com | hackerone | True | 23 | False | not selected: single-program live e2e chooses most recent eligible program |
| 2fbdcfe0-7255-497f-888f-7ff1495b490f | ratelimited | RATELIMITED | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 2f46a142-616c-4851-8557-65155f574ba0 | ycombinator | Y Combinator | hackerone | True | 6 | False | not selected: single-program live e2e chooses most recent eligible program |
| d9790fa2-c1e4-4eec-9589-1636c5d9a7da | passhash | passhash | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| 45dc06e3-e022-4044-93a8-410dcae153d2 | pingidentity | Ping Identity | hackerone | True | 10 | False | not selected: single-program live e2e chooses most recent eligible program |
| 2cd4374b-7474-4e2b-817f-a566904bc9ed | crowdstrike | Crowdstrike | hackerone | True | 19 | False | not selected: single-program live e2e chooses most recent eligible program |
| 560961c8-2bad-420a-bf05-861ff4a4e465 | affirm | Affirm | hackerone | True | 3 | False | not selected: single-program live e2e chooses most recent eligible program |
| a414ca84-f09c-4f45-b2d7-815e46f68dd7 | coalition | Coalition, Inc. | hackerone | True | 3 | False | not selected: single-program live e2e chooses most recent eligible program |
| dda96618-8834-4cfc-babe-1dc5db15669d | cosmos | Cosmos | hackerone | True | 17 | False | not selected: single-program live e2e chooses most recent eligible program |
| 60fafd88-f4a6-42a6-980b-64e189962fb3 | databricks | Databricks | hackerone | True | 5 | False | not selected: single-program live e2e chooses most recent eligible program |
| 5f524a60-478c-4225-8eaa-341e694abf6c | flutteruki | Flutter UK&I | hackerone | True | 42 | False | not selected: single-program live e2e chooses most recent eligible program |
| 99770bc0-4a69-41f6-82e3-760b3433da53 | jamieweb | JamieWeb | hackerone | True | 6 | False | not selected: single-program live e2e chooses most recent eligible program |
| 354457aa-7dc4-426f-9315-fb5ad76a3a3e | ed | Ed | hackerone | True | 6 | False | not selected: single-program live e2e chooses most recent eligible program |
| 70c8bad9-b07b-4ae2-9546-a91700ddfd81 | bitmex | BitMEX | hackerone | True | 8 | False | not selected: single-program live e2e chooses most recent eligible program |
| b4db9ca5-b6d1-4624-ae33-51ddc7b8d8b5 | smule | Smule | hackerone | True | 7 | False | not selected: single-program live e2e chooses most recent eligible program |
| 99f5d538-ad7e-4e8c-bcf7-e75f91b3de8f | fig | Fig | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| f6d29926-3daf-4514-92d6-b391e8f7d5d6 | elastic | Elastic | hackerone | True | 60 | False | not selected: single-program live e2e chooses most recent eligible program |
| 41411df5-20f1-4764-ba33-9b607eaefc0f | valve | Valve | hackerone | True | 21 | False | not selected: single-program live e2e chooses most recent eligible program |
| 12369ee1-fb66-4890-828d-037f5f878a61 | epicgames | Epic Games | hackerone | True | 85 | False | not selected: single-program live e2e chooses most recent eligible program |
| ff5f44f7-84b5-4075-8622-14fc430c7f98 | deconf_com | Deconf | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| 5eadcf25-0b60-4264-a403-3b2718eb9870 | nodejs | Node.js | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| 231cc23d-f8d4-464b-8b23-a476c6217869 | netlify | Netlify | hackerone | True | 14 | False | not selected: single-program live e2e chooses most recent eligible program |
| 395a645f-8fda-485e-825f-1c6f3b5004d9 | kartpay | Kartpay | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| e2693bfb-fb61-4085-98a4-30d88f3b6a74 | streak_com | Streak | hackerone | True | 4 | False | not selected: single-program live e2e chooses most recent eligible program |
| c607b815-fc86-49a0-8c23-d5526c4525ca | usertesting | UserTesting | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| bd68f803-bb66-4f2c-9b9b-a93833873809 | superhuman | Superhuman (formerly Grammarly) | hackerone | True | 24 | False | not selected: single-program live e2e chooses most recent eligible program |
| 0bb51995-bc1f-4b29-b1da-ce42c06ff51a | hyperledger | Linux Foundation Decentralized Trust | hackerone | True | 26 | False | not selected: single-program live e2e chooses most recent eligible program |
| b94274cf-e32d-4b08-93bf-7ee7a435c30f | upserve | Upserve  | hackerone | True | 18 | False | not selected: single-program live e2e chooses most recent eligible program |
| 230e00ec-3fed-498b-b357-fcdd272a349a | malwarebytes | Malwarebytes | hackerone | True | 36 | False | not selected: single-program live e2e chooses most recent eligible program |
| a4446391-c627-4259-a794-8fa987918a9b | delight_im | delight.im | hackerone | True | 8 | False | not selected: single-program live e2e chooses most recent eligible program |
| d64ed3f0-ecc7-4fb7-af7a-67aa5d19736c | wakatime | WakaTime | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| 6d2e6c82-8418-42b3-af11-1a317eb3339a | yoti | Yoti | hackerone | True | 10 | False | not selected: single-program live e2e chooses most recent eligible program |
| 9fceae7f-57e6-4f5f-be7f-d04776b1ab49 | infogram | Infogram | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| 961b3766-6ddf-4c98-9e16-256aaf5495a6 | bumble | Bumble | hackerone | True | 50 | False | not selected: single-program live e2e chooses most recent eligible program |
| 89a9fe01-6ad8-4116-8493-7c2a3d1c6c3b | wink_jq3al | WINK | hackerone | True | 1 | False | not selected: single-program live e2e chooses most recent eligible program |
| a8935f9c-e3fa-40e9-b117-92eaa2e83018 | omise | Omise | hackerone | True | 7 | False | not selected: single-program live e2e chooses most recent eligible program |
| a3e6da23-751a-460c-861f-883c63cee88b | bitwarden | Bitwarden | hackerone | True | 18 | False | not selected: single-program live e2e chooses most recent eligible program |
| b973e214-6904-4a36-ae9b-a6b8779a88cf | parrot_sec | Parrot Sec | hackerone | True | 2 | False | not selected: single-program live e2e chooses most recent eligible program |
| 0495cdc2-2f7a-4a4c-8a45-82331cc636fa | stellar | Stellar.org | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| dafaef72-05eb-4cea-850c-6a28f5e01832 | teradici | Teradici | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| edeaf83f-6e9f-4452-ba0a-bdbdc2a38653 | autodesk | Autodesk | hackerone | True | 0 | False | no non-empty in_scope scope entries |
| 37314144-6a37-4eb2-9570-0ba319f0cd94 | rocket_chat | Rocket.Chat | hackerone | True | 5 | False | not selected: single-program live e2e chooses most recent eligible program |
| 5039f25c-dca8-468b-a3cc-6088d5061ac5 | roblox | Roblox | hackerone | True | 7 | False | not selected: single-program live e2e chooses most recent eligible program |
| 6e7f4e62-7a0f-400b-a9da-398c648161cb | weblate | Weblate | hackerone | True | 6 | False | not selected: single-program live e2e chooses most recent eligible program |

### Program Scope Used
| scope_type | asset_type | value | notes |
| --- | --- | --- | --- |
| in_scope | domain | host.docker.internal | known-vuln-target-host |
| in_scope | url | http://host.docker.internal:3001 | known-vuln-target-url |

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
    "program_id": "82f21365-d27c-5352-a67f-af2eb0fddc8a",
    "status": "queued"
  },
  "status_code": 200
}
```

### Final Scan Row
```json
{
  "completed_at": "2026-03-25T13:04:20.580373+00:00",
  "created_at": "2026-03-25T13:03:48.059208+00:00",
  "error_detail": null,
  "finding_count": 0,
  "partial_detail": null,
  "program_id": "82f21365-d27c-5352-a67f-af2eb0fddc8a",
  "retry_count": 0,
  "scan_id": "a3c9c33f-60e4-44fc-a95e-51eaee0542dd",
  "severity_breakdown": "{\"low\": 0, \"high\": 0, \"info\": 0, \"medium\": 0, \"critical\": 0}",
  "started_at": "2026-03-25T13:03:48.059208+00:00",
  "status": "completed"
}
```

### Scan Wait Result
```json
{
  "status_at_snapshot": "completed",
  "terminal_reached": true,
  "timeout_seconds": 3600
}
```

### Pipeline Stage Timeline
| stage_number | stage_name | status | started_at | completed_at | error_detail |
| --- | --- | --- | --- | --- | --- |
| 1.0 | asset_discovery | completed | 2026-03-25T13:03:48.147127+00:00 | 2026-03-25T13:04:20.569175+00:00 |  |
| 10.1 | report_handoff | completed | 2026-03-25T13:04:20.586605+00:00 | 2026-03-25T13:04:20.600104+00:00 |  |

### Artifact Counts
```json
{
  "assets_count": 0,
  "endpoints_count": 0,
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
    "completed_at": "2026-03-25T13:04:20.580373+00:00",
    "error_detail": null,
    "finding_count": 0,
    "program_id": "82f21365-d27c-5352-a67f-af2eb0fddc8a",
    "scan_id": "a3c9c33f-60e4-44fc-a95e-51eaee0542dd",
    "severity_breakdown": {
      "critical": 0,
      "high": 0,
      "info": 0,
      "low": 0,
      "medium": 0
    },
    "started_at": "2026-03-25T13:03:48.059208+00:00",
    "status": "completed"
  },
  "status_code": 200,
  "url": "http://localhost:8002/api/v1/scans/a3c9c33f-60e4-44fc-a95e-51eaee0542dd"
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
  "url": "http://localhost:8002/api/v1/scans/a3c9c33f-60e4-44fc-a95e-51eaee0542dd/findings"
}
```

## Forced Deep Trace (Downstream Replay)
_Not executed._

## Process Evidence
### Command: docker compose up -d
- Return code: `0`
- Command: `docker compose -f C:\Users\Home\Desktop\Projects\Attackbot_v1\infra\docker-compose.yml --env-file C:\Users\Home\Desktop\Projects\Attackbot_v1\.env up -d`

```text
STDOUT:
<empty>

STDERR:
 Container attackbot-vault-1  Running
 Container attackbot-rabbitmq-1  Running
 Container attackbot-loki-1  Running
 Container attackbot-prometheus-1  Running
 Container attackbot-redis-1  Running
 Container attackbot-minio-1  Running
 Container attackbot-neo4j-1  Running
 Container attackbot-grafana-1  Running
 Container attackbot-postgres-1  Running
 Container attackbot-core-engine-1  Running
 Container attackbot-reporter-1  Running
 Container attackbot-attack-graph-engine-1  Running
 Container attackbot-scraper-1  Running
 Container attackbot-scenario-runner-1  Running
 Container attackbot-reporter-worker-1  Running
 Container attackbot-api-fuzzer-worker-1  Running
 Container attackbot-browser-worker-1  Running
 Container attackbot-api-gateway-1  Running
 Container attackbot-js-analysis-worker-1  Running
 Container attackbot-core-worker-1  Running
 Container attackbot-exploit-verifier-1  Running
 Container attackbot-ai-analysis-worker-1  Running
 Container attackbot-tempo-1  Starting
 Container attackbot-vault-1  Waiting
 Container attackbot-minio-1  Waiting
 Container attackbot-postgres-1  Waiting
 Container attackbot-tempo-1  Started
 Container attackbot-vault-1  Healthy
 Container attackbot-vault-init-1  Starting
 Container attackbot-minio-1  Healthy
 Container attackbot-minio-init-1  Starting
 Container attackbot-postgres-1  Healthy
 Container attackbot-migrate-1  Starting
 Container attackbot-minio-init-1  Started
 Container attackbot-vault-init-1  Started
 Container attackbot-migrate-1  Started
 Container attackbot-migrate-1  Waiting
 Container attackbot-neo4j-1  Waiting
 Container attackbot-migrate-1  Waiting
 Container attackbot-migrate-1  Waiting
 Container attackbot-postgres-1  Waiting
 Container attackbot-minio-init-1  Waiting
 Container attackbot-redis-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-postgres-1  Waiting
 Container attackbot-migrate-1  Waiting
 Container attackbot-redis-1  Waiting
 Container attackbot-minio-init-1  Waiting
 Container attackbot-postgres-1  Waiting
 Container attackbot-redis-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-minio-init-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-redis-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-postgres-1  Healthy
 Container attackbot-redis-1  Healthy
 Container attackbot-minio-init-1  Exited
 Container attackbot-postgres-1  Healthy
 Container attackbot-minio-init-1  Exited
 Container attackbot-postgres-1  Healthy
 Container attackbot-minio-init-1  Exited
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-redis-1  Healthy
 Container attackbot-neo4j-1  Healthy
 Container attackbot-migrate-1  Exited
 Container attackbot-reporter-1  Waiting
 Container attackbot-migrate-1  Exited
 Container attackbot-migrate-1  Exited
 Container attackbot-core-engine-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-redis-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-rabbitmq-1  Waiting
 Container attackbot-migrate-1  Exited
 Container attackbot-reporter-1  Waiting
 Container attackbot-attack-graph-engine-1  Waiting
 Container attackbot-scraper-1  Waiting
 Container attackbot-core-engine-1  Waiting
 Container attackbot-reporter-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-reporter-1  Healthy
 Container attackbot-scraper-1  Healthy
 Container attackbot-redis-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-attack-graph-engine-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-core-engine-1  Healthy
 Container attackbot-rabbitmq-1  Healthy
 Container attackbot-rabbitmq-1  Healthy

```

### Command: docker compose ps
- Return code: `0`
- Command: `docker compose -f C:\Users\Home\Desktop\Projects\Attackbot_v1\infra\docker-compose.yml --env-file C:\Users\Home\Desktop\Projects\Attackbot_v1\.env ps`

```text
STDOUT:
NAME                              IMAGE                           COMMAND                  SERVICE               CREATED              STATUS                         PORTS
attackbot-ai-analysis-worker-1    attackbot-ai-analysis-worker    "celery -A backend.sâ€¦"   ai-analysis-worker    30 hours ago         Up 4 minutes                   
attackbot-api-fuzzer-worker-1     attackbot-api-fuzzer-worker     "celery -A backend.sâ€¦"   api-fuzzer-worker     30 hours ago         Up 4 minutes                   
attackbot-api-gateway-1           attackbot-api-gateway           "uvicorn backend.serâ€¦"   api-gateway           30 hours ago         Up 4 minutes (unhealthy)       0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
attackbot-attack-graph-engine-1   attackbot-attack-graph-engine   "uvicorn backend.serâ€¦"   attack-graph-engine   30 hours ago         Up 4 minutes (healthy)         8006/tcp
attackbot-browser-worker-1        attackbot-browser-worker        "celery -A backend.sâ€¦"   browser-worker        30 hours ago         Up 4 minutes                   
attackbot-core-engine-1           attackbot-core-engine           "uvicorn backend.serâ€¦"   core-engine           30 hours ago         Up 3 minutes (healthy)         0.0.0.0:8002->8002/tcp, [::]:8002->8002/tcp
attackbot-core-worker-1           attackbot-core-worker           "celery -A backend.sâ€¦"   core-worker           About a minute ago   Up About a minute              8002/tcp
attackbot-exploit-verifier-1      attackbot-exploit-verifier      "celery -A backend.sâ€¦"   exploit-verifier      30 hours ago         Up 4 minutes                   
attackbot-grafana-1               grafana/grafana:latest          "/run.sh"                grafana               30 hours ago         Up 4 minutes                   0.0.0.0:3000->3000/tcp, [::]:3000->3000/tcp
attackbot-js-analysis-worker-1    attackbot-js-analysis-worker    "celery -A backend.sâ€¦"   js-analysis-worker    30 hours ago         Up 4 minutes                   
attackbot-loki-1                  grafana/loki:latest             "/usr/bin/loki -confâ€¦"   loki                  30 hours ago         Up 4 minutes                   3100/tcp
attackbot-minio-1                 minio/minio                     "/usr/bin/docker-entâ€¦"   minio                 30 hours ago         Up 4 minutes (healthy)         9000/tcp
attackbot-neo4j-1                 neo4j:5-community               "tini -g -- /startupâ€¦"   neo4j                 30 hours ago         Up 4 minutes (healthy)         7473-7474/tcp, 7687/tcp
attackbot-postgres-1              postgres:16                     "docker-entrypoint.sâ€¦"   postgres              30 hours ago         Up 4 minutes (healthy)         0.0.0.0:5432->5432/tcp, [::]:5432->5432/tcp
attackbot-prometheus-1            prom/prometheus:latest          "/bin/prometheus --câ€¦"   prometheus            30 hours ago         Up 4 minutes                   9090/tcp
attackbot-rabbitmq-1              rabbitmq:3-management           "docker-entrypoint.sâ€¦"   rabbitmq              30 hours ago         Up 4 minutes (healthy)         0.0.0.0:15672->15672/tcp, [::]:15672->15672/tcp
attackbot-redis-1                 redis:7-alpine                  "docker-entrypoint.sâ€¦"   redis                 30 hours ago         Up 4 minutes (healthy)         6379/tcp
attackbot-reporter-1              attackbot-reporter              "uvicorn backend.serâ€¦"   reporter              30 hours ago         Up 3 minutes (healthy)         8003/tcp
attackbot-reporter-worker-1       attackbot-reporter-worker       "celery -A backend.sâ€¦"   reporter-worker       30 hours ago         Up 4 minutes                   8003/tcp
attackbot-scenario-runner-1       attackbot-scenario-runner       "celery -A backend.sâ€¦"   scenario-runner       30 hours ago         Up 4 minutes                   
attackbot-scraper-1               attackbot-scraper               "uvicorn backend.serâ€¦"   scraper               30 hours ago         Up 3 minutes (healthy)         0.0.0.0:8001->8001/tcp, [::]:8001->8001/tcp
attackbot-tempo-1                 grafana/tempo:latest            "/tempo"                 tempo                 30 hours ago         Restarting (1) 3 seconds ago   
attackbot-vault-1                 hashicorp/vault:1.15            "docker-entrypoint.sâ€¦"   vault                 30 hours ago         Up 4 minutes (healthy)         8200/tcp


STDERR:
<empty>
```

### Command: docker compose logs (tail 300)
- Return code: `0`
- Command: `docker compose -f C:\Users\Home\Desktop\Projects\Attackbot_v1\infra\docker-compose.yml --env-file C:\Users\Home\Desktop\Projects\Attackbot_v1\.env logs --no-color --since 2026-03-25T13:03:26Z --tail 300 scraper core-engine core-worker reporter reporter-worker`

```text
STDOUT:
reporter-worker-1  | [2026-03-25 13:04:20,595: WARNING/MainProcess] {"queue": "report.jobs", "event_id": "105fe4e9-71d5-434f-8037-cc17719c59ed", "event_type": "scan.completed", "scan_id": "a3c9c33f-60e4-44fc-a95e-51eaee0542dd", "program_id": "82f21365-d27c-5352-a67f-af2eb0fddc8a", "finding_count": 0, "severity_breakdown": {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}, "event": "report_job_received", "service": "reporter-worker", "level": "info", "timestamp": "2026-03-25T13:04:20.594462Z"}
reporter-worker-1  | [2026-03-25 13:04:20,595: WARNING/MainProcess] {"scan_id": "a3c9c33f-60e4-44fc-a95e-51eaee0542dd", "formats_requested": ["pdf", "docx"], "include_evidence_screenshots": true, "event": "report_job_formats_requested", "service": "reporter-worker", "level": "info", "timestamp": "2026-03-25T13:04:20.595712Z"}
reporter-worker-1  | [2026-03-25 13:04:20,596: WARNING/MainProcess] {"scan_id": "a3c9c33f-60e4-44fc-a95e-51eaee0542dd", "program_id": "82f21365-d27c-5352-a67f-af2eb0fddc8a", "event": "report_generation_not_yet_implemented", "service": "reporter-worker", "level": "warning", "timestamp": "2026-03-25T13:04:20.595999Z"}
reporter-1         | INFO:     127.0.0.1:40252 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1         | INFO:     172.20.0.9:49910 - "GET /metrics HTTP/1.1" 200 OK
reporter-1         | INFO:     127.0.0.1:42902 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     172.20.0.13:50138 - "GET /api/v1/programs/82f21365-d27c-5352-a67f-af2eb0fddc8a HTTP/1.1" 200 OK
reporter-1         | INFO:     127.0.0.1:44550 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     172.20.0.13:50138 - "GET /api/v1/programs/82f21365-d27c-5352-a67f-af2eb0fddc8a/scope HTTP/1.1" 200 OK
reporter-1         | INFO:     172.20.0.9:56442 - "GET /metrics HTTP/1.1" 200 OK
reporter-1         | INFO:     127.0.0.1:59332 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1         | INFO:     172.20.0.9:42672 - "GET /metrics HTTP/1.1" 200 OK
reporter-1         | INFO:     127.0.0.1:45952 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1         | INFO:     127.0.0.1:33936 - "GET /api/v1/health HTTP/1.1" 200 OK
reporter-1         | INFO:     172.20.0.9:35184 - "GET /metrics HTTP/1.1" 200 OK
reporter-1         | INFO:     127.0.0.1:59148 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     172.20.0.9:58148 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1          | INFO:     127.0.0.1:50348 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     127.0.0.1:38700 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     172.20.0.9:35488 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1          | INFO:     172.20.0.13:51824 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     172.20.0.12:59850 - "GET /api/v1/programs/82f21365-d27c-5352-a67f-af2eb0fddc8a/scope HTTP/1.1" 200 OK
scraper-1          | INFO:     172.20.0.13:51824 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     127.0.0.1:50252 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     172.20.0.13:36530 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     172.20.0.9:58862 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1          | INFO:     127.0.0.1:43166 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | Running job "Reconciler.reconcile (trigger: interval[0:05:00], next run at: 2026-03-25 13:09:07 UTC)" (scheduled at 2026-03-25 13:04:07.501710+00:00)
scraper-1          | {"reason": "E2E_PAUSE_RECONCILER is enabled", "event": "reconciler_paused", "service": "scraper", "level": "info", "timestamp": "2026-03-25T13:04:07.503214Z"}
scraper-1          | Job "Reconciler.reconcile (trigger: interval[0:05:00], next run at: 2026-03-25 13:09:07 UTC)" executed successfully
scraper-1          | INFO:     172.20.0.13:50484 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     127.0.0.1:52714 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     172.20.0.9:35302 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1          | INFO:     172.20.0.13:41800 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     127.0.0.1:44766 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     172.20.0.9:36902 - "GET /metrics HTTP/1.1" 404 Not Found
scraper-1          | INFO:     172.20.0.13:35256 - "GET /api/v1/health HTTP/1.1" 200 OK
scraper-1          | INFO:     127.0.0.1:45360 - "GET /api/v1/health HTTP/1.1" 200 OK
core-worker-1      | [2026-03-25 13:03:47,705: INFO/MainProcess] Task core_engine.scan_task[8352f9b6-70bf-46dd-a3bf-7641aa907ec2] received
core-worker-1      | [2026-03-25 13:03:47,712: WARNING/ForkPoolWorker-2] {"program_id": "82f21365-d27c-5352-a67f-af2eb0fddc8a", "event_type": "program.scraped", "event": "Scan task received", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T13:03:47.711625Z"}
core-worker-1      | [2026-03-25 13:03:47,942: WARNING/ForkPoolWorker-2] {"pool_size": 10, "max_overflow": 20, "event": "db_initialized", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T13:03:47.942574Z"}
core-worker-1      | [2026-03-25 13:03:47,944: WARNING/ForkPoolWorker-2] {"endpoint": "minio:9000", "secure": false, "event": "minio_connected", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T13:03:47.944569Z"}
core-worker-1      | [2026-03-25 13:03:48,071: WARNING/ForkPoolWorker-2] {"scan_id": "a3c9c33f-60e4-44fc-a95e-51eaee0542dd", "program_id": "82f21365-d27c-5352-a67f-af2eb0fddc8a", "event": "Scan created", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T13:03:48.071100Z"}
core-worker-1      | [2026-03-25 13:03:48,124: INFO/ForkPoolWorker-2] HTTP Request: GET http://scraper:8001/api/v1/programs/82f21365-d27c-5352-a67f-af2eb0fddc8a/scope "HTTP/1.1 200 OK"
core-worker-1      | [2026-03-25 13:03:48,146: WARNING/ForkPoolWorker-2] {"url": "amqp://attackbot:attackbot@rabbitmq:5672/", "event": "queue_publisher_connected", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T13:03:48.146022Z"}
core-worker-1      | [2026-03-25 13:03:48,146: WARNING/ForkPoolWorker-2] {"scan_id": "a3c9c33f-60e4-44fc-a95e-51eaee0542dd", "event": "Stage 0: Scope filter", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T13:03:48.146403Z"}
core-worker-1      | [2026-03-25 13:03:48,147: WARNING/ForkPoolWorker-2] {"in_scope_count": 2, "out_of_scope_count": 0, "event": "ScopeFilter built", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T13:03:48.146923Z"}
core-worker-1      | [2026-03-25 13:03:48,148: WARNING/ForkPoolWorker-2] {"args": "subfinder", "timeout": 180, "event": "Running subfinder[host.docker.internal]", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T13:03:48.148435Z"}
core-worker-1      | [2026-03-25 13:04:19,513: WARNING/ForkPoolWorker-2] {"domain": "host.docker.internal", "event": "alterx_skipped_no_subfinder_results", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T13:04:19.512794Z"}
core-worker-1      | [2026-03-25 13:04:19,514: WARNING/ForkPoolWorker-2] {"args": "dnsx", "timeout": 270, "event": "Running dnsx[host.docker.internal]", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T13:04:19.514659Z"}
core-worker-1      | [2026-03-25 13:04:20,564: WARNING/ForkPoolWorker-2] {"scan_id": "a3c9c33f-60e4-44fc-a95e-51eaee0542dd", "seed_domains": 1, "assets_found": 0, "errors": 0, "event": "Stage 1 complete", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T13:04:20.564248Z"}
core-worker-1      | [2026-03-25 13:04:20,577: WARNING/ForkPoolWorker-2] {"scan_id": "a3c9c33f-60e4-44fc-a95e-51eaee0542dd", "event": "No assets found \u2014 skipping Stages 2\u20136", "service": "core-worker", "level": "warning", "timestamp": "2026-03-25T13:04:20.577189Z"}
core-worker-1      | [2026-03-25 13:04:20,597: WARNING/ForkPoolWorker-2] {"queue": "report.jobs", "event_type": "scan.completed", "event_id": "105fe4e9-71d5-434f-8037-cc17719c59ed", "event": "message_published", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T13:04:20.597216Z"}
core-worker-1      | [2026-03-25 13:04:20,604: WARNING/ForkPoolWorker-2] {"scan_id": "a3c9c33f-60e4-44fc-a95e-51eaee0542dd", "event": "Published scan.completed to report.jobs", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T13:04:20.604036Z"}
core-worker-1      | [2026-03-25 13:04:20,604: WARNING/ForkPoolWorker-2] {"scan_id": "a3c9c33f-60e4-44fc-a95e-51eaee0542dd", "findings_saved": 0, "status": "completed", "breakdown": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}, "event": "Stage 10 complete", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T13:04:20.604311Z"}
core-worker-1      | [2026-03-25 13:04:20,606: WARNING/ForkPoolWorker-2] {"event": "queue_publisher_closed", "service": "core-worker", "level": "info", "timestamp": "2026-03-25T13:04:20.606160Z"}
core-worker-1      | [2026-03-25 13:04:20,612: INFO/ForkPoolWorker-2] Task core_engine.scan_task[8352f9b6-70bf-46dd-a3bf-7641aa907ec2] succeeded in 32.90783368199999s: None
core-engine-1      | HTTP Request: GET http://scraper:8001/api/v1/programs/82f21365-d27c-5352-a67f-af2eb0fddc8a "HTTP/1.1 200 OK"
core-engine-1      | HTTP Request: GET http://scraper:8001/api/v1/programs/82f21365-d27c-5352-a67f-af2eb0fddc8a/scope "HTTP/1.1 200 OK"
core-engine-1      | {"check": "nuclei", "detail": "/usr/local/bin/nuclei", "event": "worker_toolchain_check_ok", "service": "core-engine", "level": "info", "timestamp": "2026-03-25T13:03:47.574857Z"}
core-engine-1      | {"check": "nuclei_templates", "detail": "Command '['nuclei', '-tl']' timed out after 20 seconds", "event": "worker_toolchain_check_failed", "service": "core-engine", "level": "warning", "timestamp": "2026-03-25T13:03:47.575399Z"}
core-engine-1      | INFO:     172.20.0.1:48040 - "POST /api/v1/scans/start HTTP/1.1" 200 OK
core-engine-1      | INFO:     172.20.0.9:60522 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1      | INFO:     172.20.0.9:40410 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1      | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1      | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1      | INFO:     127.0.0.1:37212 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1      | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1      | INFO:     127.0.0.1:35518 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1      | INFO:     172.20.0.9:44536 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1      | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1      | INFO:     127.0.0.1:58654 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1      | INFO:     172.20.0.9:34710 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1      | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1      | INFO:     127.0.0.1:43198 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1      | INFO:     172.20.0.9:37940 - "GET /metrics HTTP/1.1" 404 Not Found
core-engine-1      | Running job "recover_stuck_scans (trigger: interval[0:05:00], next run at: 2026-03-25 13:09:33 UTC)" (scheduled at 2026-03-25 13:04:33.425565+00:00)
core-engine-1      | Job "recover_stuck_scans (trigger: interval[0:05:00], next run at: 2026-03-25 13:09:33 UTC)" executed successfully
core-engine-1      | HTTP Request: GET http://scraper:8001/api/v1/health "HTTP/1.1 200 OK"
core-engine-1      | INFO:     127.0.0.1:57006 - "GET /api/v1/health HTTP/1.1" 200 OK
core-engine-1      | INFO:     172.20.0.1:32806 - "GET /api/v1/scans/a3c9c33f-60e4-44fc-a95e-51eaee0542dd HTTP/1.1" 200 OK
core-engine-1      | INFO:     172.20.0.1:45114 - "GET /api/v1/scans/a3c9c33f-60e4-44fc-a95e-51eaee0542dd/findings HTTP/1.1" 200 OK
core-engine-1      | INFO:     172.20.0.1:45116 - "GET /api/v1/queue/dlq/inspect HTTP/1.1" 200 OK


STDERR:
<empty>
```

### Command: docker compose logs reporter-worker (tail 300)
- Return code: `0`
- Command: `docker compose -f C:\Users\Home\Desktop\Projects\Attackbot_v1\infra\docker-compose.yml --env-file C:\Users\Home\Desktop\Projects\Attackbot_v1\.env logs --no-color --since 2026-03-25T13:03:26Z --tail 300 reporter-worker`

```text
STDOUT:
reporter-worker-1  | [2026-03-25 13:04:20,595: WARNING/MainProcess] {"queue": "report.jobs", "event_id": "105fe4e9-71d5-434f-8037-cc17719c59ed", "event_type": "scan.completed", "scan_id": "a3c9c33f-60e4-44fc-a95e-51eaee0542dd", "program_id": "82f21365-d27c-5352-a67f-af2eb0fddc8a", "finding_count": 0, "severity_breakdown": {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}, "event": "report_job_received", "service": "reporter-worker", "level": "info", "timestamp": "2026-03-25T13:04:20.594462Z"}
reporter-worker-1  | [2026-03-25 13:04:20,595: WARNING/MainProcess] {"scan_id": "a3c9c33f-60e4-44fc-a95e-51eaee0542dd", "formats_requested": ["pdf", "docx"], "include_evidence_screenshots": true, "event": "report_job_formats_requested", "service": "reporter-worker", "level": "info", "timestamp": "2026-03-25T13:04:20.595712Z"}
reporter-worker-1  | [2026-03-25 13:04:20,596: WARNING/MainProcess] {"scan_id": "a3c9c33f-60e4-44fc-a95e-51eaee0542dd", "program_id": "82f21365-d27c-5352-a67f-af2eb0fddc8a", "event": "report_generation_not_yet_implemented", "service": "reporter-worker", "level": "warning", "timestamp": "2026-03-25T13:04:20.595999Z"}


STDERR:
<empty>
```

## Observed Gaps in Current Implementation
- Reporter worker currently validates `report.jobs` envelopes only.
- Specialist workers are queue listeners; deeper stages land in later milestones.
- This report reflects what ran in this test session, not aspirational docs.
