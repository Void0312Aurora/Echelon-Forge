# Echelon Forge Cordis Runtime Package

该 package 同时包含已接受的 P2-C1 producer seam 与已接受的有界 P6-A
package-maturation surface。它使用 Cordis 的 `Context`、plugin、event、service、injection、effect 与
fiber-disposal primitive，把仓库自有的 `builtin.default_compatibility` package lower
为冻结的 `RuntimeCompositionRequest`。

P6-A surface 增加严格版本化 schema 和公开 SDK helper，用于：

- 定义仓库自有 package 与 configuration overlay；
- 确定性解析依赖，并拒绝缺失依赖和依赖环；
- 固定 profile module、profile bundle、overlay 的原始字节，以及精确 Cordis
  版本和 package lock；
- 生成与 request、catalog lock、profile projection identity 绑定的 canonical
  package provenance；
- 为 native-validation handoff 生成稳定且不包含本机路径的 diagnostics。

package descriptor 不拥有 provider、backend 选择、component contribution 或 system
order；这些仍由 owner-admitted 仓库 artifact 与 native validator 掌握。本有界切片唯一
准入的 overlay 只是重述冻结的默认配置；任何改变 truth 的 overlay 都会因不再匹配已准入
request/catalog-lock identity 而被拒绝。更广可配置 profile 仍是后续 admission 切片。

```text
npm install
npm test
npm run produce -- --out build/default-profile
```

CLI 还会输出 `runtime_package_provenance.v1.json` 与
`runtime_package_diagnostics.v1.json`，并保留既有 request、lock、authority、projection、
requested/resolved manifest 与 metadata 文件。支持的 SDK 从
`@echelon-forge/cordis-runtime` 导入；契约和仓库自有定义通过明确的 subpath export 暴露。

未知 profile、未固定字节、依赖环、overlay 冲突、修改后的配置以及缺失 catalog-lock
artifact 都会在 native handoff 前失败。外部 package 签名、任意第三方 plugin、更广
profile、Node hosting、CUDA parity 与 JavaScript 仿真 stepping 不属于本有界切片。
