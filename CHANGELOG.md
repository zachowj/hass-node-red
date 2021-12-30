# Changelog

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
