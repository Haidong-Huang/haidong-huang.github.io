# 个人主页上线说明

目标网址：**https://haidong-huang.github.io/**

这个地址对应 GitHub 账号 `Haidong-Huang`，无需购买域名或服务器，也无需配置 DNS。网页中显示的名字仍是 **Haidong (Andrew) Huang**。修改显示名字不会改变网址。

## 1. 修改仓库名称

打开 https://github.com/Haidong-Huang/homepage ，点击 **Settings → General**。在 **Repository name** 中，把 `homepage` 改为 `haidong-huang.github.io`，点击 **Rename**。保留 Public。文件和提交记录随仓库保留，无需重新使用模板。

改名后仓库地址：https://github.com/Haidong-Huang/haidong-huang.github.io

`_config.yml` 已准备为：

```yaml
url: "https://haidong-huang.github.io"
baseurl: ""
repository: "Haidong-Huang/haidong-huang.github.io"
```

如果保留 `homepage` 仓库名，网址将是 `https://haidong-huang.github.io/homepage/`，需要同时调整路径和自动部署设置。本次按个人主页根网址准备。

## 2. 开启 GitHub Pages

在改名后的仓库点击 **Settings → Pages**。

- **Build and deployment → Source** 选择 **GitHub Actions**。
- **Custom domain 留空**：它只用于另行购买的独立域名，不填写 `haidong-huang.github.io`。
- 不需要新增 `CNAME` 文件。
- 若界面提供 **Enforce HTTPS**，保持开启。

仓库已准备 `.github/workflows/pages.yml`，无需再创建第二份工作流。

## 3. 将准备好的网站合并到 main

如果已提供网站更新的 Pull Request（合并请求）链接，打开链接，等待 **Build and check Jekyll site** 成功。如果仍为 Draft，先点击 **Ready for review**，然后点击 **Merge pull request → Confirm merge**。

合并请求只负责审阅和构建；合并到 `main` 后才发布。工作流会检查仓库名称，避免把根网址版本发布到 `/homepage/` 路径。

如果没有在线合并请求，可以使用 `release/haidong-huang-homepage-source.zip` 作为上传源。先解压，通过 GitHub Desktop 等 Git 客户端同步完整目录到仓库根目录，务必包含隐藏的 `.github` 文件夹。不要上传 ZIP 文件本身，也不要把内容再套进一个 `homepage` 子文件夹。同名模板文件用本次版本替换。

## 4. 等待发布并打开网站

在仓库 **Actions → Build and deploy homepage** 查看最新运行。两个任务都应成功：

1. **Build and check Jekyll site**：生成正式网站，检查图片、内部链接和索引文件。
2. **Publish to GitHub Pages**：发布网站。

然后点击 **Settings → Pages → Visit site**，或直接访问 https://haidong-huang.github.io/ 。首次发布可能需要几分钟；GitHub 文档提示更新可能需要约 10 分钟。

如果代码先合并、Pages 后开启，或改名时已有构建完成：在 **Actions → Build and deploy homepage → Run workflow** 选择 `main`，重新运行即可。

浏览器地址栏输入完整网址即可访问。通过搜索引擎搜索姓名找到网站，需要搜索引擎后续收录，时间不由 GitHub 控制。

## 后续更新

编辑 `_data/profile.yml`、`_news/` 或 `_publications/`，同步到 `main` 后网站会自动更新。仅修改本地文件不会同步到公网。

本地仍可双击 `preview.cmd`，然后打开 http://127.0.0.1:4000/ 。该地址只在这台电脑上有效。

本次准备了网页分享信息、规范网址、`sitemap.xml`、`robots.txt` 和 404 页面。原始图片导入目录、预览缓存和维护文档不会进入公开网页。

## 出现问题时

| 现象 | 检查位置 |
| --- | --- |
| 构建红色失败 | Actions 中打开失败的步骤查看日志 |
| Publish 被跳过 | 仓库是否叫 `haidong-huang.github.io`，是否运行 `main` |
| Configure GitHub Pages 失败 | Settings → Pages 的 Source 是否为 GitHub Actions |
| 网页 404 | 发布任务是否成功、是否使用正确网址 |
| 图片或样式 404 | `baseurl` 是否为空、是否上传完整 assets 目录 |

官方说明：[创建个人 Pages 网站](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)、[Actions 自定义发布](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)、[仓库改名](https://docs.github.com/en/repositories/creating-and-managing-repositories/renaming-a-repository)。
