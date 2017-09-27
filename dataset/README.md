# whale.run services - dataset

## 系统环境变量设置

    FLASK_LOGFILE (default: whalerun_dataset.log)
    FLASK_MYSQL_HOST (default: localhost)
    FLASK_MYSQL_PORT (default: 3306)
    FLASK_MYSQL_USER (default: root)
    FLASK_MYSQL_PASSWORD
    FLASK_MYSQL_DB (default: whalerun_dataset)
    FLASK_REDIS_HOST (default: localhost)
    FLASK_REDIS_PORT (default: 6379)
    FLASK_REDIS_DB (default: 0)
    OSS_REGION_ID
    OSS_BUCKET_NAME
    OSS_MOUNT_POINT

## API Overview

**All data is sent and received as JSON.**

**success response**

    {
        code: 0
        message: 'Success'
        data: {
            [响应数据]
        }
    }

**error response**

    {
        code: [错误码]
        message: [错误信息]
        data: {}
    }

**错误码对应错误信息**

    1000: 'Internal Server Error'
    1100: 'Bad Request'
    1101: 'Unauthorized'
    1103: 'Forbidden'
    1104: 'Not Found'
    1201: 'GET方法url参数不完整'
    1202: 'GET方法url参数值错误'
    1401: 'POST/PUT方法json数据不完整'
    1402: 'POST/PUT方法json数据值或类型错误'
    1430: 'oss对象不存在'
    1431: '数据集文件异常'
    1601: 'DELETE方法url参数不完整'
    1602: 'DELETE方法url参数值错误'

**某些情况下通用的错误码**

    所有请求：1000
    POST/PUT方法：1100
    使用分页参数page/per_page：1202

**通用的可选URL参数**

    fields: 指定返回的对象数据中只包含哪些字段，多个字段以英文逗号分隔

## API References

**创建数据集文件**

    POST  /api/dataset_files/

    必填数据字段：
        user_id [int]: 用户id
        name [string]: 文件名
        oss_object [string]: 源文件oss存储对象
        size [int]: 源文件大小，以字节记

    可选数据字段：
        mime_type [string]: MIME类型
        description [string]: 描述

    响应数据：
        dataset_file [object]:

    错误码：
        1401, 1402, 1430

**列出数据集**

    GET  /api/datasets/

    可选URL参数：
        ids: 数据集id，多个值以英文逗号分隔
        uuids: 数据集uuid，多个值以英文逗号分隔
        user_ids: 用户id，多个值以英文逗号分隔
        order_by:
        page:
        per_page:
        hidden: 是否隐藏：0 - 否，1 - 是
        featured: 是否推荐：0 - 否，1 - 是

    响应数据：
        datasets [object_array]:
        total [int]:

    错误码：
        1202

**创建数据集**

    POST  /api/datasets/

    必填数据字段：
        user_id [int]: 用户id
        title [string]: 标题
        description [string]: 描述
        license [string]: 许可证名称
        file_ids [int_array]: 数据集文件id数组

    响应数据：
        dataset [object]:

    错误码：
        1401, 1402, 1431

**编辑数据集**

    PUT  /api/datasets/<int:dataset_id>/

    必填数据字段：
        user_id [int]: 用户id
        title [string]: 标题
        description [string]: 描述
        license [string]: 许可证名称
        file_ids [int_array]: 数据集文件id数组

    响应数据：
        dataset [object]:

    错误码：
        1103, 1104, 1401, 1402, 1431

**更新数据集是否隐藏**

    PUT  /api/datasets/<int:dataset_id>/hidden/

    必填数据字段：
        user_id [int]: 用户id
        hidden [bool]: 是否隐藏

    响应数据：
        dataset [object]:

    错误码：
        1103, 1104, 1401, 1402

**更新数据集的笔记个数**

    PUT  /api/datasets/<int:dataset_id>/total_notebooks/

    必填数据字段：
        delta [int]: 笔记的增/减数

    响应数据：
        dataset [object]:

    错误码：
        1104, 1401, 1402

**更新数据集的话题个数**

    PUT  /api/datasets/<int:dataset_id>/total_topics/

    必填数据字段：
        delta [int]: 话题的增/减数

    响应数据：
        dataset [object]:

    错误码：
        1104, 1401, 1402

**更新数据集的评论个数**

    PUT  /api/datasets/<int:dataset_id>/total_comments/

    必填数据字段：
        delta [int]: 评论的增/减数

    响应数据：
        dataset [object]:

    错误码：
        1104, 1401, 1402

**更新数据集的点赞个数**

    PUT  /api/datasets/<int:dataset_id>/total_votes/

    必填数据字段：
        delta [int]: 点赞的增/减数

    响应数据：
        dataset [object]:

    错误码：
        1104, 1401, 1402

## Model Dependencies

_- : on_delete='CASCADE'_

_* : on_delete='CASCADE', null=True_

**Dataset**

    * : DatasetFile

**DatasetFile**

    * : DatasetFile
