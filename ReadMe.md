# Amazon Q Developer 自动代码审核 - GitHub版

## 简介

基于Amazon Q Developer的GitHub代码审核实现基于以下流程：

1. 开发者提交代码或创建Pull Request
2. GitHub Actions工作流触发
3. 使用预配置的Docker镜像运行Amazon Q Developer CLI进行代码审核
4. Amazon Q Developer CLI分析代码变更并生成审核报告
5. 审核结果作为评论添加到Pull Request中

GitHub中的项目仓库结构如下：
```
.
├── .github/
│   └── workflows/
│       └── code-review.yml  # GitHub Actions工作流配置
├── Dockerfile.github        # GitHub Actions运行时所用docker镜像
├── github_comment.py        # 审核结束调用GitHub API填写评论的代码
├── ewallet                  # 测试使用的代码,在您的环境中，此为您的项目代码
└── improve_rules/           # 审核规则
    ├── improved_code_review_standards_part1.md # 代码风格和代码质量
    ├── improved_code_review_standards_part2.md # 功能实现、安全性和性能
    ├── improved_code_review_standards_part3.md # 测试、日志记录、可维护性和特定场景
    ├── improved_code_review_standards_part4.md # 语言特定检查点、中间件使用指南等
    └── llm_code_review_feedback_format.md      # 审核报告规则
```
审核结果样例[参考此](static/amazon_q_review_16098438007.md)。此样例为对新增文件ewallet/controller/top_up.py的代码审核。

## 如何使用？


本指南将帮助您将基于 Amazon Q Developer 的代码审核流程集成到 GitHub 仓库中。

## 流程概述

基于 Amazon Q Developer 的 GitHub 代码审核实现基于以下流程：

1. 开发者提交代码或创建 Pull Request
2. GitHub Actions 工作流触发
3. 使用预配置的 Docker 镜像运行 Amazon Q Developer CLI 进行代码审核
4. Amazon Q Developer CLI 分析代码变更并生成审核报告
5. 审核结果作为评论添加到 Pull Request 中

## 设置步骤

### 0. Repo添加代码审核所需文件
添加本repo中.github、improve_rules、github_comment.py  到待审核的repo的根目录下


### 1. 构建并推送 Docker 镜像
* 获取Github密钥推送镜像

   首先，您需要获取推送镜像到Docker 镜像仓库的密钥（如果您已经有此密钥，或者您不使用Docker的镜像仓库，则可忽略此步骤），
   * 在 GitHub 任何页面的右上角，点击你的个人头像，然后点击"设置"（Settings）。

   * 在左侧边栏，点击"开发者设置"（Developer settings）。

   * 在左侧边栏的"个人访问令牌"（Personal access tokens）下，点击"令牌（经典）"（Tokens (classic)）。

   * 选择"生成新令牌"（Generate new token），然后点击"生成新令牌（经典）"（Generate new token (classic)）。

   * 在"备注"（Note）字段中，为你的令牌起一个描述性的名称。

   * 要为你的令牌设置过期时间，选择"过期时间"（Expiration），然后选择一个默认选项或点击"自定义"（Custom）输入日期。

   * 选择 repo 和 packages两个权限

   * 点击"生成令牌"（Generate token）。

    ![alt text](<img/截屏2025-07-06 13.06.49.png>)

   更详细的说明可参考官方文档：[如何获取Github Access Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-personal-access-token-classic)、[如何获取具有repo权限的Github Token](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)。
  

* 推送镜像

  构建 Docker 镜像并将其推送到 GitHub Container Registry：

   ```bash
   # 登录到 GitHub Container Registry
   GITHUB_TOKEN="xxxxx" # 替换为上一步创建的Token
   USER_NAME="xxx" # 替换为您的用户名
   YOUR_ORG="xxxx" #替换为您的 GitHub 组织或用户名。
   echo $GITHUB_TOKEN | docker login ghcr.io -u ${USER_NAME} --password-stdin 
   
   # 构建 Docker 镜像
   docker build -f Dockerfile.github -t ghcr.io/${YOUR_ORG}/amazon-q-code-review:latest .

   # 推送镜像到 GitHub Container Registry
   docker push ghcr.io/${YOUR_ORG}/amazon-q-code-review:latest
   ```

   确保将 `YOUR-ORG` 替换为您的 GitHub 组织或用户名。

* 设置镜像仓库权限

   * 打开packages，选择刚刚上传的镜像，选择package setting，然后添加需要审核代码的repo
   ![alt text](<img/截屏2025-07-06 13.44.56.png>)
   ![alt text](<img/截屏2025-07-06 13.45.20.png>)
   ![alt text](<img/截屏2025-07-06 13.46.29.png>)

### 2. 设置Amazon Q developer CLI的凭证

在一台Linux服务器中[安装并登录Amazon Q CLI](https://docs.aws.amazon.com/zh_cn/amazonq/latest/qdeveloper-ug/command-line-installing.html#command-line-installing-ubuntu)，然后执行以下命令，将Amazon Q developer 登录凭证保存到s3
```
aws s3 sync ~/.local/share/amazon-q s3://${S3BucketName}/amazonq-credentials/amazon-q
```
注意：此凭证最长90天过期，所以需要定时轮换。

### 3. 配置 GitHub 仓库变量和密钥

所有密钥和变量需要在GitHub仓库的设置中配置。路径为：
**仓库 > Settings > Secrets and variables > Actions**

此流程需要一个AWS IAM用户以及AK/SK，用于下载第2步中上传的Q CLI凭证，建议只给该用户以下权限：
```

{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:GetObjectVersion",
                "s3:ListBucket",
                "s3:GetBucketLocation",
                "s3:GetBucketVersioning"
            ],
            "Resource": [
                "arn:aws:s3:::xxxxx", #将xxxxx替换为你的s3桶
                "arn:aws:s3:::xxxxx/*"
            ]
        }
    ]
}
```

1. **GITHUB_TOKEN**
   - 描述：GitHub自动提供的令牌，用于在PR中添加评论
   - 在仓库设置中启用适当的权限：
     - 路径：仓库 > Settings > Actions > General > Workflow permissions
     - 选择："Read and write permissions"

   此处为了快速验证，我们使用了默认权限，业务流程中，请使用最小权限，关于GitHub Token权限的详细说明，请参考[官方文档](https://docs.github.com/en/actions/how-tos/security-for-github-actions/security-guides/automatic-token-authentication#permissions-for-the-github_token)。
 ![alt text](<img/截屏2025-07-06 12.57.40.png>)
 ![alt text](<img/截屏2025-07-06 12.57.04.png>)
  
2. **AWS_ACCESS_KEY_ID**
   - 位置：仓库 > Settings > Secrets and variables > Actions > New repository secret
   - 描述：AWS访问密钥ID
   - 用途：如果需要从S3同步Amazon Q配置
   - 获取方式：AWS IAM控制台

3. **AWS_SECRET_ACCESS_KEY**
   - 位置：仓库 > Settings > Secrets and variables > Actions > New repository secret
   - 描述：AWS秘密访问密钥
   - 用途：与AWS_ACCESS_KEY_ID配对使用
   - 获取方式：AWS IAM控制台

4. **AWS_REGION**
   - 位置：仓库 > Settings > Secrets and variables > Actions > New repository secret
   - 描述：AWS区域
   - 用途：指定S3桶所在的区域
   - 示例值：us-east-1, ap-northeast-1等，为存储Amazon Q developer cli密钥的S3桶所在的区域

5. **AMAZON_Q_S3_URI**
   - 位置：仓库 > Settings > Secrets and variables > Actions > New repository secret
   - 描述：Amazon Q配置的S3 URI
   - 用途：指定从哪个S3位置同步Amazon Q配置
   - 格式：s3://{Your_bucket_name}/amazonq-credentials/amazon-q

设置完相关仓库变量后如下：
![alt text](<img/截屏2025-07-06 13.32.47.png>)

### 3. 更新工作流文件

编辑 `.github/workflows/code-review.yml` 文件，将 Docker 镜像路径更新为您推送的镜像：

```yaml
env:
  DOCKER_IMAGE: ghcr.io/YOUR-ORG/amazon-q-code-review:latest  # 替换为您的镜像
```


## 使用方法

### 自动代码审核

当创建或更新 Pull Request 时，代码审核工作流将自动触发。审核完成后，结果将作为评论添加到 PR 中。


### 手动触发代码审核

您也可以手动触发代码审核：

1. 转到仓库的 Actions 标签页
2. 选择 "Amazon Q Code Review" 工作流
3. 点击 "Run workflow"
4. 选择要审核的分支
5. 选择审核类型（"full" 或 "changes"）
6. 点击 "Run workflow" 按钮

## 注意事项

1. 对于大型代码库，全库审核可能需要较长时间
2. 如果审核结果超过 GitHub 评论大小限制（约 65KB），系统将创建一个 Gist 并在评论中提供链接
3. 确保 Docker 镜像有足够的权限访问您的代码和创建评论

## 故障排除

如果遇到问题，请检查：

1. GitHub Actions 日志以获取详细错误信息
2. 确保所有必要的 Secrets 已正确设置
3. 验证 Docker 镜像是否可以访问并正确配置
4. 检查 GitHub 令牌是否有足够的权限

### 常见问题

1. **Amazon Q无法进行代码审核**
   - 检查REGISTRATION_TOKEN是否正确设置
   - 确认Docker镜像中已正确安装Amazon Q CLI

2. **无法访问GitHub Container Registry**
   - 检查仓库权限设置
   - 确认Docker登录凭证是否有效

3. **审核结果未添加到PR**
   - 检查GITHUB_TOKEN权限
   - 查看github_comment.py脚本的执行日志


## 使用方法

### 自动代码审核

当创建或更新Pull Request时，代码审核工作流将自动触发。审核完成后，结果将作为评论添加到PR中。

### 手动触发代码审核

您也可以手动触发代码审核：

1. 转到仓库的Actions标签页
2. 选择"Amazon Q Code Review"工作流
3. 点击"Run workflow"
4. 选择要审核的分支
5. 选择审核类型（"full"或"changes"）
6. 点击"Run workflow"按钮

## 故障排除

如果遇到问题，请检查：

1. GitHub Actions日志以获取详细错误信息
2. 确保所有必要的Secrets已正确设置
3. 验证Docker镜像是否可以访问并正确配置
4. 检查GitHub令牌是否有足够的权限

## 注意事项

1. 对于大型代码库，全库审核可能需要较长时间
2. 如果审核结果超过GitHub评论大小限制（约65KB），系统将创建一个Gist并在评论中提供链接
3. 确保Docker镜像有足够的权限访问您的代码和创建评论
