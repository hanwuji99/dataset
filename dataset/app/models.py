# -*- coding: utf-8 -*-

import datetime
from uuid import uuid1

from flask import current_app
from peewee import *
from playhouse.shortcuts import model_to_dict

from . import db
from .constants import DEFAULT_PER_PAGE


_to_set = (lambda r: set(r) if r else set())
_nullable_strip = (lambda s: s.strip() or None if s else None)


class BaseModel(Model):
    """
    所有model的基类
    """
    id = PrimaryKeyField()  # 主键
    uuid = UUIDField(unique=True, default=uuid1)  # UUID
    create_time = DateTimeField(default=datetime.datetime.now)  # 创建时间
    update_time = DateTimeField(default=datetime.datetime.now)  # 更新时间
    weight = IntegerField(default=0)  # 排序权重

    class Meta:
        database = db
        only_save_dirty = True

    @classmethod
    def _exclude_fields(cls):
        """
        转换为dict表示时排除在外的字段
        :return:
        """
        return {'create_time', 'update_time'}

    @classmethod
    def _extra_attributes(cls):
        """
        转换为dict表示时额外增加的属性
        :return:
        """
        return {'iso_create_time', 'iso_update_time'}

    @classmethod
    def query_by_id(cls, _id):
        """
        根据id查询
        :param _id:
        :return:
        """
        obj = None
        try:
            obj = cls.get(cls.id == _id)
        finally:
            return obj

    @classmethod
    def query_by_uuid(cls, _uuid):
        """
        根据uuid查询
        :param _uuid:
        :return:
        """
        obj = None
        try:
            obj = cls.get(cls.uuid == _uuid)
        finally:
            return obj

    @classmethod
    def count(cls, select_query=None):
        """
        根据查询条件计数
        :param select_query: [SelectQuery or None]
        :return:
        """
        cnt = 0
        try:
            if select_query is None:
                select_query = cls.select()
            cnt = select_query.count()
        finally:
            return cnt

    @classmethod
    def iterator(cls, select_query=None, order_by=None, page=None, per_page=None):
        """
        根据查询条件返回迭代器
        :param select_query: [SelectQuery or None]
        :param order_by: [iterable or None]
        :param page:
        :param per_page:
        :return:
        """
        try:
            if select_query is None:
                select_query = cls.select()

            if order_by:
                _fields = cls._meta.fields
                clauses = []
                for item in order_by:
                    desc, attr = item.startswith('-'), item.lstrip('+-')
                    if attr in cls._exclude_fields():
                        continue
                    if attr in cls._extra_attributes():
                        attr = attr.split('_', 1)[-1]
                    if attr in _fields:
                        clauses.append(_fields[attr].desc() if desc else _fields[attr])
                if clauses:
                    select_query = select_query.order_by(*clauses)

            if page or per_page:
                select_query = select_query.paginate(int(page or 1), int(per_page or DEFAULT_PER_PAGE))

            return select_query.naive().iterator()

        except Exception, e:
            current_app.logger.error(e)
            return iter([])

    def to_dict(self, only=None, exclude=None, recurse=False, backrefs=False, max_depth=None):
        """
        转换为dict表示
        :param only: [iterable or None]
        :param exclude: [iterable or None]
        :param recurse: [bool]
        :param backrefs: [bool]
        :param max_depth:
        :return:
        """
        try:
            only = _to_set(only)
            exclude = _to_set(exclude) | self._exclude_fields()

            _fields = self._meta.fields
            only_fields = {_fields[k] for k in only if k in _fields}
            exclude_fields = {_fields[k] for k in exclude if k in _fields}
            extra_attrs = self._extra_attributes() - exclude
            if only:
                extra_attrs &= only
                if not only_fields:
                    exclude_fields = _fields.values()

            return model_to_dict(self, recurse=recurse, backrefs=backrefs, only=only_fields, exclude=exclude_fields,
                                 extra_attrs=extra_attrs, max_depth=max_depth)

        except Exception, e:
            current_app.logger.error(e)
            return {}

    def modified_fields(self, exclude=None):
        """
        与数据库中对应的数据相比，数值有变动的字段名称列表
        :param exclude: [iterable or None]
        :return:
        """
        try:
            exclude = _to_set(exclude)
            db_obj = self.query_by_id(self.id)
            return filter(lambda f: getattr(self, f) != getattr(db_obj, f) and f not in exclude,
                          self._meta.sorted_field_names)

        except Exception, e:
            current_app.logger.error(e)

    def change_weight(self, weight):
        """
        修改排序权重
        :param weight:
        :return:
        """
        try:
            self.weight = weight
            self.save()
            return self

        except Exception, e:
            current_app.logger.error(e)

    def iso_create_time(self):
        return self.create_time.isoformat()

    def iso_update_time(self):
        return self.update_time.isoformat()


class Dataset(BaseModel):
    """
    数据集
    """
    user_id = IntegerField(index=True)  # 用户id

    title = CharField()  # 标题
    description = TextField()  # 描述
    license = CharField()  # 许可证名称
    source = CharField(null=True)  # 源文件url
    oss_object = CharField(null=True)  # 源文件oss存储对象
    size = BigIntegerField(null=True)  # 源文件大小，以字节记

    total_files = IntegerField()  # 文件个数
    total_views = IntegerField(default=0)  # 浏览次数
    total_downloads = IntegerField(default=0)  # 下载次数

    total_votes = IntegerField(default=0)  # 点赞个数
    total_topics = IntegerField(default=0)  # 话题个数
    total_comments = IntegerField(default=0)  # 评论个数
    total_notebooks = IntegerField(default=0)  # 笔记个数

    hidden = BooleanField(default=False)  # 是否隐藏
    featured = BooleanField(default=False)  # 是否推荐

    class Meta:
        db_table = 'dataset'

    @classmethod
    def create_dataset(cls, user_id, title, description, license, total_files):
        """
        创建数据集
        :param user_id: 
        :param title: 
        :param description: 
        :param license: 
        :param total_files: 
        :return: 
        """
        try:
            return cls.create(
                user_id=user_id,
                title=title.strip(),
                description=description,
                license=license.strip(),
                total_files=total_files
            )

        except Exception, e:
            current_app.logger.error(e)

    def update_dataset(self, title, description, license, total_files):
        """
        更新数据集
        :param title: 
        :param description: 
        :param license: 
        :param total_files: 
        :return: 
        """
        try:
            self.title = title.strip()
            self.description = description
            self.license = license.strip()
            self.total_files = total_files
            self.update_time = datetime.datetime.now()
            self.save()
            return self

        except Exception, e:
            current_app.logger.error(e)


class DatasetFile(BaseModel):
    """
    数据集文件
    """
    user_id = IntegerField(index=True)  # 用户id
    dataset = ForeignKeyField(Dataset, on_delete='CASCADE', null=True)  # 外键联结Dataset
    parent = ForeignKeyField('self', related_name='children', on_delete='CASCADE', null=True)  # 外键自联结

    name = CharField()  # 文件名/表名
    mime_type = CharField(null=True)  # MIME类型
    file_format = CharField(null=True)  # 文件格式
    description = TextField(null=True)  # 描述
    source = CharField(null=True)  # 源文件url
    oss_object = CharField(null=True)  # 源文件oss存储对象
    size = BigIntegerField(null=True)  # 源文件大小，以字节记
    preview = TextField(null=True)  # 预览数据

    class Meta:
        db_table = 'dataset_file'

    @classmethod
    def _exclude_fields(cls):
        return BaseModel._exclude_fields() | {'preview'}

    @classmethod
    def _extra_attributes(cls):
        return BaseModel._extra_attributes() | {'array_preview'}

    @classmethod
    def create_dataset_files(cls, user_id, name, parent=None, mime_type=None, file_format=None, description=None,
                             source=None, oss_object=None, size=None, preview=None):
        """
        创建数据集文件
        :param user_id: 
        :param name: 
        :param parent: 
        :param mime_type: 
        :param file_format: 
        :param description: 
        :param source: 
        :param oss_object: 
        :param size: 
        :param preview: [list or None]
        :return: 
        """
        try:
            return cls.create(
                user_id=user_id,
                parent=parent,
                name=name.strip(),
                mime_type=_nullable_strip(mime_type),
                file_format=_nullable_strip(file_format),
                description=_nullable_strip(description),
                source=_nullable_strip(source),
                oss_object=_nullable_strip(oss_object),
                size=size,
                preview=repr(preview) if preview else None
            )

        except Exception, e:
            current_app.logger.error(e)

    def array_preview(self):
        return eval(self.preview) if self.preview else []


class Board(BaseModel):
    """
    板块
    """
    board_id = IntegerField(index=True)  # 板块id
    name = CharField()  # 标题
    total_datasets = IntegerField()  # 数据集个数
    oss_object = CharField(null=True)  # 源文件oss存储对象 板块图片
    last_update = DateTimeField(default=datetime.datetime.now)  # 最后活跃时间

    class Meta:
        db_table = 'board'

    @classmethod
    def create_board(cls,board_id, name, total_datasets,oss_object,last_update):
        """
        创建板块
        :param board_id:
        :param name:
        :param total_datasets:
        :param oss_object:
        :param last_update:
        :return:
        """
        try:
            return cls.create(
                board_id=board_id,
                name=name.strip(),
                total_datasets=total_datasets,
                oss_object=_nullable_strip(oss_object),
                last_update = last_update,
            )
        except Exception, e:
            current_app.logger.error(e)

    @classmethod
    def all_board(cls):
        pass

    @classmethod
    def update_board(cls):
        pass



models = [Dataset, DatasetFile,Board]
