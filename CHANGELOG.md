# Changelog

## What's Changed
* build(deps): bump actions/setup-python from 3 to 4 by @dependabot in https://github.com/zachowj/hass-node-red/pull/154
* build(deps): bump actions/stale from 3 to 6 by @dependabot in https://github.com/zachowj/hass-node-red/pull/153
* build(deps): bump GoogleCloudPlatform/release-please-action from 2 to 3 by @dependabot in https://github.com/zachowj/hass-node-red/pull/152
* build(deps): bump pre-commit/action from 2.0.3 to 3.0.0 by @dependabot in https://github.com/zachowj/hass-node-red/pull/151
* build(deps): bump actions/stale from 6 to 7 by @dependabot in https://github.com/zachowj/hass-node-red/pull/159
* Grammar correction by @Z0mbiel0ne in https://github.com/zachowj/hass-node-red/pull/164
* chore: Update version by @zachowj in https://github.com/zachowj/hass-node-red/pull/167

## New Contributors
* @dependabot made their first contribution in https://github.com/zachowj/hass-node-red/pull/154
* @Z0mbiel0ne made their first contribution in https://github.com/zachowj/hass-node-red/pull/164
* @zachowj made their first contribution in https://github.com/zachowj/hass-node-red/pull/167

**Full Changelog**: https://github.com/zachowj/hass-node-red/compare/v1.1.2...v1.1.3

## [4.2.3](https://github.com/zachowj/hass-node-red/compare/v4.2.2...v4.2.3) (2026-01-28)


### Tests

* **websocket:** add tests for webhook allowed methods validation and device trigger removal on connection close ([80580dd](https://github.com/zachowj/hass-node-red/commit/80580dddcf75728cd6b3dbd477ed11ab6d572540))


### Continuous Integration

* **pre-commit:** pre-commit autoupdate ([#387](https://github.com/zachowj/hass-node-red/issues/387)) ([fe8216a](https://github.com/zachowj/hass-node-red/commit/fe8216a80c326f0e9447a4948b208f59cc885d0d))
* **pre-commit:** pre-commit autoupdate ([#389](https://github.com/zachowj/hass-node-red/issues/389)) ([b914867](https://github.com/zachowj/hass-node-red/commit/b9148676978b47fd91d39bd0c247d8eb38fdfdba))
* **pre-commit:** pre-commit autoupdate ([#390](https://github.com/zachowj/hass-node-red/issues/390)) ([435a165](https://github.com/zachowj/hass-node-red/commit/435a165dcf1c74c46cdec4bc7e132e0b8b0f001f))

## [4.2.2](https://github.com/zachowj/hass-node-red/compare/v4.2.1...v4.2.2) (2026-01-05)


### Bug Fixes

* **device_trigger:** add Context type hint to forward_trigger function ([558308c](https://github.com/zachowj/hass-node-red/commit/558308c697082ed60e5e85cb1821bb8f19fc2130))
* **text:** enforce maximum state length for text entities ([629a9e9](https://github.com/zachowj/hass-node-red/commit/629a9e93a4e58a0f90328a8fed2dee8d6afa77cf))


### Tests

* refactor tests for select and switch entities to improve clarity and structure ([4074c4d](https://github.com/zachowj/hass-node-red/commit/4074c4d62e6286f6cb639cfe58950c53d0f66ed4))
* refactor tests to improve clarity and structure ([a055bc0](https://github.com/zachowj/hass-node-red/commit/a055bc081c2f7975958643ac86927991e0495c25))
* replace direct FakeConnection instantiation with fixture usage ([042b7f7](https://github.com/zachowj/hass-node-red/commit/042b7f78906e80227ff7d3202fc7cd26df94ed68))

## [4.2.1](https://github.com/zachowj/hass-node-red/compare/v4.2.0...v4.2.1) (2026-01-04)


### Bug Fixes

* **webhook:** correct payload data in webhook response ([f5bbcb7](https://github.com/zachowj/hass-node-red/commit/f5bbcb7afbdaec6503eec281abb47bd324c05f17))
* **webhook:** unregister webhooks when integration is unloaded ([f5bbcb7](https://github.com/zachowj/hass-node-red/commit/f5bbcb7afbdaec6503eec281abb47bd324c05f17))

## [4.2.0](https://github.com/zachowj/hass-node-red/compare/v4.1.5...v4.2.0) (2026-01-03)


### Features

* **number:** allow dynamic updates of min, max, step, mode, and unit ([7539127](https://github.com/zachowj/hass-node-red/commit/7539127a9232a42481d56b4d15d532ed37bf7a42))
* **sensor:** accept numeric and ISO timestamp values for date and timestamp ([7539127](https://github.com/zachowj/hass-node-red/commit/7539127a9232a42481d56b4d15d532ed37bf7a42))


### Bug Fixes

* **text:** handle numeric values without throwing errors ([7539127](https://github.com/zachowj/hass-node-red/commit/7539127a9232a42481d56b4d15d532ed37bf7a42))


### Documentation

* Correct search term to 'hass-node-red' in README ([8a05951](https://github.com/zachowj/hass-node-red/commit/8a05951171d74ef6756dd179e3a7d70e6115cc27)), closes [#382](https://github.com/zachowj/hass-node-red/issues/382)
* Revise Node-RED installation steps in README ([#377](https://github.com/zachowj/hass-node-red/issues/377)) ([e89e76b](https://github.com/zachowj/hass-node-red/commit/e89e76bf1b3a60b53af8bdc3b877e50c687397ca))


### Styles

* fix ruff linting issues ([7539127](https://github.com/zachowj/hass-node-red/commit/7539127a9232a42481d56b4d15d532ed37bf7a42)), closes [#383](https://github.com/zachowj/hass-node-red/issues/383)
* update code to comply with new Ruff rules ([4563bac](https://github.com/zachowj/hass-node-red/commit/4563bacb09062d52389fe3436dab9add16fbd906))


### Code Refactoring

* extract NodeRedEntity into separate module ([7539127](https://github.com/zachowj/hass-node-red/commit/7539127a9232a42481d56b4d15d532ed37bf7a42))


### Build System

* **deps:** bump astral-sh/setup-uv from 4 to 7 ([#373](https://github.com/zachowj/hass-node-red/issues/373)) ([644eedb](https://github.com/zachowj/hass-node-red/commit/644eedb2e42fda7a91373ba1cdbde942b25b41db))


### Continuous Integration

* **pre-commit:** pre-commit autoupdate ([#379](https://github.com/zachowj/hass-node-red/issues/379)) ([4653cd7](https://github.com/zachowj/hass-node-red/commit/4653cd703289754d7821d6bac493a7729b21ef0d))
* **pre-commit:** pre-commit autoupdate ([#381](https://github.com/zachowj/hass-node-red/issues/381)) ([8e570b9](https://github.com/zachowj/hass-node-red/commit/8e570b9d22657816ed1ac53eb9c333bbbd2af0ab))


### Miscellaneous Chores

* remove VSCode launch and settings configuration files ([4563bac](https://github.com/zachowj/hass-node-red/commit/4563bacb09062d52389fe3436dab9add16fbd906))
* update pre-commit configuration and add ruff settings ([666854c](https://github.com/zachowj/hass-node-red/commit/666854c54f26925ab595f76609cb3d3da35a29c4))

## [4.1.5](https://github.com/zachowj/hass-node-red/compare/v4.1.4...v4.1.5) (2025-12-08)


### Bug Fixes

* fix hass.config_entries.async_forward_entry_setups warning ([6dab7d4](https://github.com/zachowj/hass-node-red/commit/6dab7d4f25935682f75fe5c1fe458e5f8883e113)), closes [#368](https://github.com/zachowj/hass-node-red/issues/368)


### Code Refactoring

* replace pip with uv for package management and update README instructions ([22c2e5e](https://github.com/zachowj/hass-node-red/commit/22c2e5ec1f44fa6b868c31d47ab98dde144103c3))


### Build System

* update devcontainer configuration and setup script for improved environment setup ([350d179](https://github.com/zachowj/hass-node-red/commit/350d1792d16b2d8ad06366f12557254e93a3fd38))


### Continuous Integration

* update pip install commands to use --system flag for consistency ([1991fa2](https://github.com/zachowj/hass-node-red/commit/1991fa2e883a545123a78e23b1eb45e67ffeb4f7))

## [4.1.4](https://github.com/zachowj/hass-node-red/compare/v4.1.3...v4.1.4) (2025-12-07)


### Bug Fixes

* properly unsubscribe from discovery listeners when the component unloads ([ec149e8](https://github.com/zachowj/hass-node-red/commit/ec149e8e40fd677bea4153b97deef1a4ac9a76f0))


### Documentation

* add Node-RED Companion AI guide with architecture overview and developer workflows ([7065841](https://github.com/zachowj/hass-node-red/commit/7065841268076a892be1e0d1cfa2f19bf1682dd5))


### Code Refactoring

* streamline discovery flow and entity management for Node-RED components ([ec149e8](https://github.com/zachowj/hass-node-red/commit/ec149e8e40fd677bea4153b97deef1a4ac9a76f0)), closes [#333](https://github.com/zachowj/hass-node-red/issues/333) [#331](https://github.com/zachowj/hass-node-red/issues/331)


### Build System

* **deps:** bump actions/checkout from 4 to 5 ([#353](https://github.com/zachowj/hass-node-red/issues/353)) ([ca761bf](https://github.com/zachowj/hass-node-red/commit/ca761bf69a81917bfcaccda926b1284876cd24ac))
* **deps:** bump actions/checkout from 5 to 6 ([#367](https://github.com/zachowj/hass-node-red/issues/367)) ([d025401](https://github.com/zachowj/hass-node-red/commit/d025401d360c03d441b36de778614a1dbe2b0c9b))
* **deps:** bump actions/github-script from 7 to 8 ([#354](https://github.com/zachowj/hass-node-red/issues/354)) ([b61750e](https://github.com/zachowj/hass-node-red/commit/b61750e08f404bf81f0a6d8eaba9edf33845ded4))
* **deps:** bump actions/setup-python from 5 to 6 ([#351](https://github.com/zachowj/hass-node-red/issues/351)) ([e40bcb6](https://github.com/zachowj/hass-node-red/commit/e40bcb6b04bf5d57f717ddd695631036d9e0785d))
* **deps:** bump actions/stale from 9 to 10 ([#352](https://github.com/zachowj/hass-node-red/issues/352)) ([edac0e3](https://github.com/zachowj/hass-node-red/commit/edac0e3d780d6fb9a1f851952e4ed62736b1797d))
* **deps:** bump colorlog from 6.9.0 to 6.10.1 ([#360](https://github.com/zachowj/hass-node-red/issues/360)) ([0c981ed](https://github.com/zachowj/hass-node-red/commit/0c981ed30edbd04e29a012372761c06247de2014))
* **deps:** update pip requirement from &lt;25.1,&gt;=21.0 to &gt;=21.0,&lt;25.3 ([#349](https://github.com/zachowj/hass-node-red/issues/349)) ([82c9213](https://github.com/zachowj/hass-node-red/commit/82c9213059208faa3177b34b627517cb1db1a26d))
* **deps:** update pip requirement from &lt;25.3,&gt;=21.0 to &gt;=21.0,&lt;25.4 ([#363](https://github.com/zachowj/hass-node-red/issues/363)) ([54a0ab6](https://github.com/zachowj/hass-node-red/commit/54a0ab66be875bf84f8ddf087a4ed6f0aff5780c))


### Continuous Integration

* **pre-commit:** pre-commit autoupdate ([#357](https://github.com/zachowj/hass-node-red/issues/357)) ([1cbc447](https://github.com/zachowj/hass-node-red/commit/1cbc4474258ced2be312b58cc5156627480fddcc))
* **pre-commit:** pre-commit autoupdate ([#359](https://github.com/zachowj/hass-node-red/issues/359)) ([c1b9662](https://github.com/zachowj/hass-node-red/commit/c1b966207e3bb5987c70c666071364da0dc85d84))
* **pre-commit:** pre-commit autoupdate ([#362](https://github.com/zachowj/hass-node-red/issues/362)) ([9ce6155](https://github.com/zachowj/hass-node-red/commit/9ce615510a2637b9f662b0095e96457f96882d11))
* **workflows:** add conditional check for beta channel in validation job ([b7e35fa](https://github.com/zachowj/hass-node-red/commit/b7e35facf670b2e6f91ec5c38b379d19e79143d9))
* **workflows:** add phac_version parameter to test jobs and update installation logic ([05f4eea](https://github.com/zachowj/hass-node-red/commit/05f4eea039df505e93d3f63e8fbd7d10b6560803))
* **workflows:** add workflow_call trigger to run_tests.yml ([983b07d](https://github.com/zachowj/hass-node-red/commit/983b07dc2d8eaea42c53d19874e672d96fd30994))
* **workflows:** comment out specific matrix configuration for HA version 2024.5.0 ([8752f8f](https://github.com/zachowj/hass-node-red/commit/8752f8f99182543bad3347c416eb4a8d459fba01))
* **workflows:** refactor pull and push workflows to include tests ([7dde0a5](https://github.com/zachowj/hass-node-red/commit/7dde0a5d9733588eb350d5be73f3a997af68297d))
* **workflows:** simplify validation jobs and reintroduce beta validation ([95ae875](https://github.com/zachowj/hass-node-red/commit/95ae8759eebb87bfe33583b4c0cce94596e4d7ff))
* **workflows:** update PHAC_VERSION installation logic for pytest-homeassistant-custom-component ([9603fe6](https://github.com/zachowj/hass-node-red/commit/9603fe69c6b2ca75a4b6e0613a4d4f1815b76751))


### Miscellaneous Chores

* **scripts:** update file permissions to executable for dev, lint, setup, test, and version scripts ([dbc3e60](https://github.com/zachowj/hass-node-red/commit/dbc3e60ebd16da0f288c906f0a72e579dc8b9778))

## [4.1.3](https://github.com/zachowj/hass-node-red/compare/v4.1.2...v4.1.3) (2025-09-28)


### Bug Fixes

* **sentence:** update trigger registration for compatibility with newer Home Assistant versions ([b167475](https://github.com/zachowj/hass-node-red/commit/b167475442475012bf737a94188f385b72fd8558)), closes [#346](https://github.com/zachowj/hass-node-red/issues/346)
* **websocket:** use call_soon_threadsafe for sending messages in websocket_device_trigger ([680897b](https://github.com/zachowj/hass-node-red/commit/680897b2414490fe522277960f56b8e22cf5f2f7))


### Build System

* **deps:** update pip requirement from &lt;24.4,&gt;=21.0 to &gt;=21.0,&lt;25.1 ([#332](https://github.com/zachowj/hass-node-red/issues/332)) ([18c2cde](https://github.com/zachowj/hass-node-red/commit/18c2cde78ce0de0b1313c382a6a4556b7c542496))


### Continuous Integration

* add workflow to remove 'waiting-for-response' label on author comments and update stale workflow settings ([943d298](https://github.com/zachowj/hass-node-red/commit/943d298a67fb99f3cd8ee665339f1fda90d75039))
* **cron:** add workflow_dispatch trigger and enhance validation steps ([737b0fd](https://github.com/zachowj/hass-node-red/commit/737b0fd33a4a2021d5f4f0fc6a901264ed213f5c))
* **cron:** correct import path for Home Assistant version retrieval ([d1cf490](https://github.com/zachowj/hass-node-red/commit/d1cf4907f25d452fef23119574d8434ea388be5d))
* **pre-commit:** update ruff hook configuration ([1655c4a](https://github.com/zachowj/hass-node-red/commit/1655c4a82c04cd7b11bf94c480319b1b856fe82e))


### Miscellaneous Chores

* **pre-commit:** update dependencies for isort, ruff, bandit, and python-typing-update ([eec2aaf](https://github.com/zachowj/hass-node-red/commit/eec2aaffa65f3bb6538ecab0274bc4f62bb6d8bb))
* **release-please:** add changelog sections for better organization ([e7498fc](https://github.com/zachowj/hass-node-red/commit/e7498fc3b3a4fedd3ddf820393e35ba89708916a))
* **setup.cfg:** remove isort not_skip configuration for __init__.py ([91c21d5](https://github.com/zachowj/hass-node-red/commit/91c21d5af7734233ca36dc135359f57af21f1e81))
* update virtual environment entry to ignore all variations of .venv ([ae1f6d3](https://github.com/zachowj/hass-node-red/commit/ae1f6d3cc07c9cea4d04a63c31ddabdc09efb263))

## [4.1.2](https://github.com/zachowj/hass-node-red/compare/v4.1.1...v4.1.2) (2024-12-15)


### Bug Fixes

* **binary_sensor:** handle LockState import and use fallback for STATE_UNLOCKED ([2413954](https://github.com/zachowj/hass-node-red/commit/2413954fbc426c4fa537d83b6100d342dfeba46f))
* Replace deprecated constant ([5c3e865](https://github.com/zachowj/hass-node-red/commit/5c3e865cb344fb06f5c543886c3e91820ec61177)), closes [#307](https://github.com/zachowj/hass-node-red/issues/307)
* **sentence:** serialize RecognizeResult for JSON compatibility ([f826058](https://github.com/zachowj/hass-node-red/commit/f826058eb43c17f816e8b12670b129d81ca2f8f5)), closes [#327](https://github.com/zachowj/hass-node-red/issues/327)
* **switch:** Remove warning about using incorrect schema for entity service registration ([#312](https://github.com/zachowj/hass-node-red/issues/312)) ([8c93dd4](https://github.com/zachowj/hass-node-red/commit/8c93dd4f2b132f98bb2688867e6f0b6f8eee668e)), closes [#314](https://github.com/zachowj/hass-node-red/issues/314)

## [4.1.1](https://github.com/zachowj/hass-node-red/compare/v4.1.0...v4.1.1) (2024-09-26)


### Bug Fixes

* **sentence:** fix sentence issue in HA 2024.10.x ([8114e1b](https://github.com/zachowj/hass-node-red/commit/8114e1b7d18517f3beaf4d2c6e104b520f4a5394))

## [4.1.0](https://github.com/zachowj/hass-node-red/compare/v4.0.2...v4.1.0) (2024-09-11)


### Features

* **sentence:** add support for custom responses in the Sentence node ([80e1afa](https://github.com/zachowj/hass-node-red/commit/80e1afa00ee95c36016d1bb154a7e858eb546dd3))


### Bug Fixes

* **sentence:** Fix default value for response_type ([314ae11](https://github.com/zachowj/hass-node-red/commit/314ae119da80f10782fe9dcf9074ceb47483d57c))

## [4.0.2](https://github.com/zachowj/hass-node-red/compare/v4.0.1...v4.0.2) (2024-08-16)


### Bug Fixes

* **device:** Convert entity registry id into entity id to fix device action ([78e854a](https://github.com/zachowj/hass-node-red/commit/78e854a088d0b7463ddfce4abee97df6da7f985e))

## [4.0.1](https://github.com/zachowj/hass-node-red/compare/v4.0.0...v4.0.1) (2024-07-07)


### Bug Fixes

* Replace deprecated async_forward_entry_setup function ([89150df](https://github.com/zachowj/hass-node-red/commit/89150dffb1c78b2d9bda01528a0f1edb542e7500))

## [4.0.0](https://github.com/zachowj/hass-node-red/compare/v3.1.7...v4.0.0) (2024-05-02)


### ⚠ BREAKING CHANGES

* **sentence:** Changes made to conversation agent now require Home Assistant 2024.5+ for sentence node to work

### Bug Fixes

* **sentence:** Fix getting default conversation agent ([60e81ce](https://github.com/zachowj/hass-node-red/commit/60e81cea91c100407d0b2caa6b26d7a69a2f4fd0)), closes [#270](https://github.com/zachowj/hass-node-red/issues/270)

## [3.1.7](https://github.com/zachowj/hass-node-red/compare/v3.1.6...v3.1.7) (2024-05-02)


### Bug Fixes

* Replace deprecated HomeAssistantType with HomeAssistant ([#268](https://github.com/zachowj/hass-node-red/issues/268)) ([8730766](https://github.com/zachowj/hass-node-red/commit/873076695d9db24a6688c1a784488c8a1b129664)), closes [#267](https://github.com/zachowj/hass-node-red/issues/267)

## [3.1.6](https://github.com/zachowj/hass-node-red/compare/v3.1.5...v3.1.6) (2024-04-07)


### Bug Fixes

* **webhook:** Fix deprecated has.components.webhook ([24270d7](https://github.com/zachowj/hass-node-red/commit/24270d76122e22f4b1ed191e67e66faa3fd9e47b)), closes [#258](https://github.com/zachowj/hass-node-red/issues/258)

## [3.1.5](https://github.com/zachowj/hass-node-red/compare/v3.1.4...v3.1.5) (2024-04-06)


### Miscellaneous Chores

* release 3.1.5 ([b30c397](https://github.com/zachowj/hass-node-red/commit/b30c3977b372ac6aca5218157c3a9ae3729d3151))

## [3.1.4](https://github.com/zachowj/hass-node-red/compare/v3.1.3...v3.1.4) (2024-04-04)


### Bug Fixes

* **sentence:** Fix to handle sentence trigger signature change ([03d34da](https://github.com/zachowj/hass-node-red/commit/03d34da80d7135ce21f6f93809307be7fff53f13)), closes [#260](https://github.com/zachowj/hass-node-red/issues/260)


### Documentation

* Update README to new location to install integrations ([16b40cd](https://github.com/zachowj/hass-node-red/commit/16b40cda30b0ca11811813e7fc90d57fff431c56))

## [3.1.3](https://github.com/zachowj/hass-node-red/compare/v3.1.2...v3.1.3) (2024-01-05)


### Bug Fixes

* Fix failure during loading due to MQTT init ([#239](https://github.com/zachowj/hass-node-red/issues/239)) ([6302ea6](https://github.com/zachowj/hass-node-red/commit/6302ea688eb28979cc994680359ef25f4c57e62b))

## [3.1.2](https://github.com/zachowj/hass-node-red/compare/v3.1.1...v3.1.2) (2023-12-13)


### Bug Fixes

* **time:** Catch invalid time format ([c071fe0](https://github.com/zachowj/hass-node-red/commit/c071fe05c20833d381eeb42725c2a42b860bed83))

## [3.1.1](https://github.com/zachowj/hass-node-red/compare/v3.1.0...v3.1.1) (2023-11-05)


### Bug Fixes

* **number:** Use correct attr for unit of measurement ([4847f98](https://github.com/zachowj/hass-node-red/commit/4847f98cc728536372279ad503c27a3c519d6bd4))

## [3.1.0](https://github.com/zachowj/hass-node-red/compare/v3.0.1...v3.1.0) (2023-11-05)


### Features

* Slovak translation ([5179512](https://github.com/zachowj/hass-node-red/commit/517951220990cd428fff20662acf994e6288ab40))


### Bug Fixes

* Change sensors with the category config to none ([5607880](https://github.com/zachowj/hass-node-red/commit/56078807990de1879fb526dd9eae026465b8344f)), closes [#225](https://github.com/zachowj/hass-node-red/issues/225)

## [3.0.1](https://github.com/zachowj/hass-node-red/compare/v3.0.0...v3.0.1) (2023-10-02)


### Documentation

* Move service data to translations ([0e126a7](https://github.com/zachowj/hass-node-red/commit/0e126a7e904b9b30cbd442b8794661e2414bafc1))

## [3.0.0](https://github.com/zachowj/hass-node-red/compare/v2.2.0...v3.0.0) (2023-09-26)


### ⚠ BREAKING CHANGES

* The trigger service now only accepts output_path and message and require Home Assistant nodes version 0.57.0+
* Endpoint for device action changed location from nodered/device_action to nodered/device/action It now matches the new device trigger format

### Bug Fixes

* Fix the trigger service schema ([337330e](https://github.com/zachowj/hass-node-red/commit/337330e6420a338a495921a4e2a2c33bf8760291))


### Code Refactoring

* Create a separate endpoint for device triggers ([029f88b](https://github.com/zachowj/hass-node-red/commit/029f88b211b01b415c8894e7374eed7416bf9324))

## [2.2.0](https://github.com/zachowj/hass-node-red/compare/v2.1.1...v2.2.0) (2023-08-09)


### Features

* **sentence:** Allow custom responses ([d3b6ebe](https://github.com/zachowj/hass-node-red/commit/d3b6ebe647f0ad83a83ba33335d35d2fb27f22ed))


### Documentation

* Fix linting in README ([18243f0](https://github.com/zachowj/hass-node-red/commit/18243f07094081eef1585e93f4ca0ab20112e671))

## 2.1.1 (2023-08-02)

## What's Changed
* build(deps): update pip requirement from <23.2,>=21.0 to >=21.0,<23.3 by @dependabot in https://github.com/zachowj/hass-node-red/pull/200


**Full Changelog**: https://github.com/zachowj/hass-node-red/compare/v2.1.0...v2.1.1

## 2.1.0 (2023-07-17)

**Full Changelog**: https://github.com/zachowj/hass-node-red/compare/v2.0.0...v2.1.0

## 2.0.0 (2023-07-13)

**Full Changelog**: https://github.com/zachowj/hass-node-red/compare/v1.6.1...v2.0.0

## 1.6.1 (2023-07-13)

## What's Changed
* Create zh-CN.json by @XuyuEre in https://github.com/zachowj/hass-node-red/pull/193

## New Contributors
* @XuyuEre made their first contribution in https://github.com/zachowj/hass-node-red/pull/193

**Full Changelog**: https://github.com/zachowj/hass-node-red/compare/v1.6.0...v1.6.1

## 1.6.0 (2023-07-12)

**Full Changelog**: https://github.com/zachowj/hass-node-red/compare/v1.5.0...v1.6.0

## 1.5.0 (2023-07-12)

**Full Changelog**: https://github.com/zachowj/hass-node-red/compare/v1.4.0...v1.5.0

## 1.4.0 (2023-07-05)

**Full Changelog**: https://github.com/zachowj/hass-node-red/compare/v1.3.0...v1.4.0

## 1.3.0 (2023-07-03)

## What's Changed
* add pt-pt by @ViPeR5000 in https://github.com/zachowj/hass-node-red/pull/174
* build(deps): bump actions/stale from 7 to 8 by @dependabot in https://github.com/zachowj/hass-node-red/pull/176
* Update README.md by @GeoffState in https://github.com/zachowj/hass-node-red/pull/179

## New Contributors
* @ViPeR5000 made their first contribution in https://github.com/zachowj/hass-node-red/pull/174
* @GeoffState made their first contribution in https://github.com/zachowj/hass-node-red/pull/179

**Full Changelog**: https://github.com/zachowj/hass-node-red/compare/v1.2.0...v1.3.0

### [1.1.2](https://www.github.com/zachowj/hass-node-red/compare/v1.1.1...v1.1.2) (2022-09-30)


### Bug Fixes

* **sensor:** Update state class on new discovery message ([280061b](https://www.github.com/zachowj/hass-node-red/commit/280061b0b43ae490ce0c37ffeec61fb25d7a00f4))

### [1.1.1](https://www.github.com/zachowj/hass-node-red/compare/v1.1.0...v1.1.1) (2022-09-21)


### Bug Fixes

* Return device info ([3a10a71](https://www.github.com/zachowj/hass-node-red/commit/3a10a71a1e4ad98521233ef3504bb879ecd04358))

## [1.1.0](https://www.github.com/zachowj/hass-node-red/compare/v1.0.9...v1.1.0) (2022-09-21)


### Features

* Add websocket command to remove device ([075e0f1](https://www.github.com/zachowj/hass-node-red/commit/075e0f133169ccc3d48a37df904aa0b19e79c3f2))
* Add websocket command to update config dynamically ([075e0f1](https://www.github.com/zachowj/hass-node-red/commit/075e0f133169ccc3d48a37df904aa0b19e79c3f2))


### Bug Fixes

* Fix import that was moved in HA ([abe7411](https://www.github.com/zachowj/hass-node-red/commit/abe741126855800ad61ceaabb7961dd4de482eb9))
* Use the correct Date type for device classes ([2e23897](https://www.github.com/zachowj/hass-node-red/commit/2e238970bc19abffca6ec3da56e47516532a6250))

### [1.0.9](https://www.github.com/zachowj/hass-node-red/compare/v1.0.8...v1.0.9) (2022-07-08)


### Bug Fixes

* Remove domains key from hacs.json ([60e389e](https://www.github.com/zachowj/hass-node-red/commit/60e389ed55d55f84cac3f4dcae535134934a43ea))
* Remove iot_class from hacs.json ([8d7fa98](https://www.github.com/zachowj/hass-node-red/commit/8d7fa980e2a620289b30ea4f12d7526cfa55273d))
* remove update listener on entry unload to avoid multiple listeners ([73dfce5](https://www.github.com/zachowj/hass-node-red/commit/73dfce507ae1ad206ac0bbc8b085d2727263a19c))


### Documentation

* Create French translation. ([#132](https://www.github.com/zachowj/hass-node-red/issues/132)) ([1b1cc39](https://www.github.com/zachowj/hass-node-red/commit/1b1cc39f49837dd91852893a391ef2f5b8d473fe))

### [1.0.8](https://www.github.com/zachowj/hass-node-red/compare/v1.0.7...v1.0.8) (2022-04-15)


### Bug Fixes

* Use enum for device automation type ([205df7b](https://www.github.com/zachowj/hass-node-red/commit/205df7b8aa2a872876ce0557cb3d15abd1a89168))


### Documentation

* Add Swedish translation ([21f1932](https://www.github.com/zachowj/hass-node-red/commit/21f193207b536ebe19b0acc49d311d67d774d6a6))

### [1.0.7](https://www.github.com/zachowj/hass-node-red/compare/v1.0.6...v1.0.7) (2022-04-03)


### Bug Fixes

* Add Companion to component title in config ([7079554](https://www.github.com/zachowj/hass-node-red/commit/70795544538f3f5969f0c6557721bd4562d2cf32))


### Documentation

* Add Brazilian Portuguese Translation ([f91adb8](https://www.github.com/zachowj/hass-node-red/commit/f91adb8aaecdd81221eb8ccf48329235ac103c92))
* Add Danish translations ([#112](https://www.github.com/zachowj/hass-node-red/issues/112)) ([2a11f2e](https://www.github.com/zachowj/hass-node-red/commit/2a11f2e0d96fac862a30be7c8b273f1b1acf53ea))
* Add german translation ([#127](https://www.github.com/zachowj/hass-node-red/issues/127)) ([fcc5a4f](https://www.github.com/zachowj/hass-node-red/commit/fcc5a4f09e7a3831699b2a0da6e7b5fd5f81b3f5))
* Rename Brazilian Portuguese Translation ([#125](https://www.github.com/zachowj/hass-node-red/issues/125)) ([2a6df42](https://www.github.com/zachowj/hass-node-red/commit/2a6df4231abea31547b7951097c5e44cc5c95af7))
* Separate install instructions ([ba49e7a](https://www.github.com/zachowj/hass-node-red/commit/ba49e7ac73ec1d531df82acb8e7dcbd3f908ce14))
* Update install instructions in readme ([#117](https://www.github.com/zachowj/hass-node-red/issues/117)) ([3f9e83b](https://www.github.com/zachowj/hass-node-red/commit/3f9e83bc6584eaf7235ec79241769518aff5d19b))

### [1.0.6](https://www.github.com/zachowj/hass-node-red/compare/v1.0.5...v1.0.6) (2022-01-08)


### Bug Fixes

* Allow binary sensors and sensors to be set to unknown by setting state to null ([ab1d854](https://www.github.com/zachowj/hass-node-red/commit/ab1d854ddf4068c6c12daed3d91140474bb051f5)), closes [#102](https://www.github.com/zachowj/hass-node-red/issues/102)
* **sensor:** Convert sensor native state to a datetime when device class is set to timestamp ([90ed37a](https://www.github.com/zachowj/hass-node-red/commit/90ed37a94a4445e5975b83101d4614f2282184cd)), closes [#103](https://www.github.com/zachowj/hass-node-red/issues/103)

### [1.0.5](https://www.github.com/zachowj/hass-node-red/compare/v1.0.4...v1.0.5) (2022-01-01)


### Bug Fixes

* **button:** Add component type ([6f7bab2](https://www.github.com/zachowj/hass-node-red/commit/6f7bab2ada1b093ad487502282c49fb94d637132))

### [1.0.4](https://www.github.com/zachowj/hass-node-red/compare/v1.0.3...v1.0.4) (2021-12-31)


### Bug Fixes

* Fix unit_of_measurement being overridden in the sensor entity ([5224dc7](https://www.github.com/zachowj/hass-node-red/commit/5224dc7c51bc2b8f888b82ced714650d483cf508))

### [1.0.3](https://www.github.com/zachowj/hass-node-red/compare/v1.0.2...v1.0.3) (2021-12-31)


### Miscellaneous Chores

* Force Release 1.0.3 ([641b5ef](https://www.github.com/zachowj/hass-node-red/commit/641b5ef85ad369c0a01c04e7dc0184518eeb129f))

### [1.0.2](https://www.github.com/zachowj/hass-node-red/compare/v1.0.1...v1.0.2) (2021-12-30)


### Bug Fixes

* Change MRO for sensor so correct unit_of_measurement gets called ([d47d2dc](https://www.github.com/zachowj/hass-node-red/commit/d47d2dc76fd3993751d23a2014e3fe79a2b7824e)), closes [#95](https://www.github.com/zachowj/hass-node-red/issues/95)

### [1.0.1](https://www.github.com/zachowj/hass-node-red/compare/v1.0.0...v1.0.1) (2021-12-26)


### Bug Fixes

* Wait for HA to be in a running state before registering device triggers ([0acacdf](https://www.github.com/zachowj/hass-node-red/commit/0acacdf6fd6d7d25de2a3dadf1b5c7fcb82e4995))

## [1.0.0](https://www.github.com/zachowj/hass-node-red/compare/v0.5.4...v1.0.0) (2021-12-19)


### ⚠ BREAKING CHANGES

* Re-add extra_state_attributes as a property function

### Features

* Add state_class and last_reset to sensor class ([6a288e0](https://www.github.com/zachowj/hass-node-red/commit/6a288e002b915a1e6a704dd6b4999c7bb4a10006)), closes [#78](https://www.github.com/zachowj/hass-node-red/issues/78)
* Added button entity ([0763aec](https://www.github.com/zachowj/hass-node-red/commit/0763aec6d8dbbb31fba785278205cca59c25c101)), closes [#91](https://www.github.com/zachowj/hass-node-red/issues/91)


### Code Refactoring

* Re-add extra_state_attributes as a property function ([541297d](https://www.github.com/zachowj/hass-node-red/commit/541297d8ee6545585c86c05b455a204d3dc30a40))

### [0.5.4](https://www.github.com/zachowj/hass-node-red/compare/v0.5.3...v0.5.4) (2021-12-03)


### Miscellaneous Chores

* release 0.5.4 ([a23b9d6](https://www.github.com/zachowj/hass-node-red/commit/a23b9d6afe8f1fae2a0005eab23f61bc8a7c1702))

### [0.5.3](https://www.github.com/zachowj/hass-node-red/compare/v0.5.2...v0.5.3) (2021-11-30)


### Bug Fixes

* Fix typo in info.md ([19642c2](https://www.github.com/zachowj/hass-node-red/commit/19642c26e1c17fceedb1ab174d95e91fa17e1002)), closes [#76](https://www.github.com/zachowj/hass-node-red/issues/76)
* removed device_state_attributes ([#82](https://www.github.com/zachowj/hass-node-red/issues/82)) ([c5f7e8c](https://www.github.com/zachowj/hass-node-red/commit/c5f7e8cacdbaf3662365437d1068293cae1290da))

### [0.5.2](https://www.github.com/zachowj/hass-node-red/compare/v0.5.0...v0.5.2) (2021-05-03)


### Bug Fixes

* Add iot_class to manifest ([437f807](https://www.github.com/zachowj/hass-node-red/commit/437f807e148534769c8ac76b07542c075a6d26a1))

## [0.5.0](https://www.github.com/zachowj/hass-node-red/compare/v0.4.5...v0.5.0) (2021-04-20)


### Features

* Add device action endpoint and device trigger switch ([b717be9](https://www.github.com/zachowj/hass-node-red/commit/b717be9505c311c8c34dccd2e42d39062a786091))
* **webhook:** send query params to NR ([a17ad73](https://www.github.com/zachowj/hass-node-red/commit/a17ad73a975ba80082e6390d8520e06a0e99c952))


### Documentation

* Add companion to name ([fb971cb](https://www.github.com/zachowj/hass-node-red/commit/fb971cb2df0da65e80ef9cb871c7d6d3bc35d53c))
* Reword webhooks ([d896bc1](https://www.github.com/zachowj/hass-node-red/commit/d896bc1f7dfae37c23a97061ea7e03482bb1b198))
* Update features ([268003d](https://www.github.com/zachowj/hass-node-red/commit/268003d02ee0d138e864b07d02bf4396c6fed217)), closes [#57](https://www.github.com/zachowj/hass-node-red/issues/57)

### [0.4.5](https://www.github.com/zachowj/hass-node-red/compare/v0.4.4...v0.4.5) (2021-03-03)


### Bug Fixes

* Add version to manifest.json ([#56](https://www.github.com/zachowj/hass-node-red/issues/56)) ([94d5ebe](https://www.github.com/zachowj/hass-node-red/commit/94d5ebe3b1295aa568bd894cb3fe3b98cf18e96e))


### Documentation

* Add step about refreshing browser ([d4c24ca](https://www.github.com/zachowj/hass-node-red/commit/d4c24cac8ffdd5ccccffc9d074d87a1bd133e537))
* Update info ([aaa5423](https://www.github.com/zachowj/hass-node-red/commit/aaa54231ea482a8413128add61d79f312934aa1a))
