# -*- coding: utf-8 -*-

import os

from flask import current_app, request, g

from . import bp_api
from ...models import Dataset, DatasetFile,Board
from ...api_utils import *
from ...constants import FILE_PREVIEW_ROWS
from ...utils.preview_util import generate_csv_preview, generate_sqlite_preview

@bp_api.route('/boards/',methods=['GET'])
def list_boards():
    '''
    列出板块
    :return:
    '''
    ids, uuids, board_ids, order_by, page, per_page = map(
        request.args.get,
        ('ids', 'uuids', 'board_ids', 'order_by', 'page', 'per_page')
    )
    ids = ids.split(',') if ids else None
    uuids = uuids.split(',') if uuids else None
    board_ids = board_ids.split(',') if board_ids else None
    order_by = order_by.split(',') if order_by else None
    claim_args_digits_string(1202, *filter(None, (page, per_page)))

    select_query = Board.select()
    if ids:
        select_query = select_query.where(Board.id << ids)
    if uuids:
        select_query = select_query.where(Board.uuid << uuids)
    if board_ids:
        select_query = select_query.where(Board.board_id << board_ids)
    boards = []
    for obj in Board.iterator(select_query, order_by, page, per_page):
        item = obj.to_dict()
        # item['']
        print 'item',item
        boards.append(item)
    data = {
        'boards': boards,
        # 'total_datasets':total_datasets,
    }
    return api_success_response(data)


@bp_api.route('/dataset_files/', methods=['POST'])
def create_dataset_files():
    """
    创建数据集文件
    :return: 
    """
    user_id, name, mime_type, description, oss_object, size = map(
        g.json.get,
        ('user_id', 'name', 'mime_type', 'description', 'oss_object', 'size')
    )
    claim_args(1401, user_id, name, oss_object, size)
    claim_args_int(1402, user_id, size)
    claim_args_string(1402, *filter(None, (name, mime_type, description, oss_object)))

    source = current_app.config['OSS']['host'] + oss_object
    file_path = current_app.config['OSS']['mount_point'] + oss_object
    claim_args_true(1430, os.path.isfile(file_path))

    if mime_type == 'text/csv' or name.lower().endswith('.csv'):
        file_format = 'csv'
        preview = generate_csv_preview(file_path, FILE_PREVIEW_ROWS)
    elif name.lower().endswith('.db') or name.lower().endswith('.sqlite'):
        file_format = 'sqlite'
        _preview = generate_sqlite_preview(file_path, FILE_PREVIEW_ROWS)
        preview = _preview['db']
        preview_tables = _preview['tables']
    else:
        file_format = None
        preview = None

    dataset_file = DatasetFile.create_dataset_files(user_id, name, None, mime_type, file_format, description, source, oss_object, size, preview)
    item = dataset_file.to_dict(g.fields)
    if file_format == 'sqlite' and preview_tables:
        item['children'] = []
        for t in preview_tables:
            table_file = DatasetFile.create_dataset_files(user_id, t, dataset_file, file_format='table', preview=preview_tables[t])
            item['children'].append(table_file.to_dict(g.fields))
    data = {
        'dataset_file': item
    }
    return api_success_response(data)


@bp_api.route('/datasets/', methods=['GET'])
def list_datasets():
    """
    列出数据集
    :return:
    """
    ids, uuids, user_ids, order_by, page, per_page, hidden, featured = map(
        request.args.get,
        ('ids', 'uuids', 'user_ids', 'order_by', 'page', 'per_page', 'hidden', 'featured')
    )
    ids = ids.split(',') if ids else None
    uuids = uuids.split(',') if uuids else None
    user_ids = user_ids.split(',') if user_ids else None
    order_by = order_by.split(',') if order_by else None
    claim_args_digits_string(1202, *filter(None, (page, per_page)))
    for _arg in [hidden, featured]:
        if _arg:
            claim_args_true(1202, _arg in ['0', '1'])

    select_query = Dataset.select()
    if ids:
        select_query = select_query.where(Dataset.id << ids)
    if uuids:
        select_query = select_query.where(Dataset.uuid << uuids)
    if user_ids:
        select_query = select_query.where(Dataset.user_id << user_ids)
    if hidden:
        select_query = select_query.where(Dataset.hidden == bool(int(hidden)))
    if featured:
        select_query = select_query.where(Dataset.featured == bool(int(featured)))
    datasets = []
    for obj in Dataset.iterator(select_query, order_by, page, per_page):
        item = obj.to_dict(g.fields)
        if not g.fields or 'dataset_files' in g.fields:
            item['dataset_files'] = []
            for _file in DatasetFile.iterator(obj.datasetfile_set.where(DatasetFile.parent.is_null())):
                file_item = _file.to_dict()
                if _file.file_format == 'sqlite':
                    file_item['children'] = [_child.to_dict() for _child in DatasetFile.iterator(_file.children)]
                item['dataset_files'].append(file_item)
        datasets.append(item)
    data = {
        'datasets': datasets,
        'total': Dataset.count(select_query)
    }
    return api_success_response(data)


@bp_api.route('/datasets/', methods=['POST'])
def create_dataset():
    """
    创建数据集
    :return: 
    """
    user_id, title, description, license, file_ids = map(g.json.get, ('user_id', 'title', 'description', 'license', 'file_ids'))
    claim_args(1401, user_id, title, description, license, file_ids)
    claim_args_int(1402, user_id)
    claim_args_string(1402, title, description, license)
    claim_args_list(1402, file_ids)
    claim_args_int(1402, *file_ids)
    files = list(DatasetFile.iterator(DatasetFile.select().where(DatasetFile.id << file_ids)))
    for f in files:
        claim_args_true(1431, f.user_id == user_id and not f.dataset and not f.parent)

    dataset = Dataset.create_dataset(user_id, title, description, license, len(files))
    for f in files:
        f.dataset = dataset
        f.save()
    data = {
        'dataset': dataset.to_dict(g.fields)
    }
    return api_success_response(data)


@bp_api.route('/datasets/<int:dataset_id>/', methods=['PUT'])
def update_dataset(dataset_id):
    """
    编辑数据集
    :param dataset_id: 
    :return: 
    """
    user_id, title, description, license, file_ids = map(g.json.get, ('user_id', 'title', 'description', 'license', 'file_ids'))
    dataset = Dataset.query_by_id(dataset_id)
    claim_args_true(1104, dataset)
    claim_args(1401, user_id, title, description, license, file_ids)
    claim_args_int(1402, user_id)
    claim_args_string(1402, title, description, license)
    claim_args_list(1402, file_ids)
    claim_args_int(1402, *file_ids)
    claim_args_true(1103, dataset.user_id == user_id)
    files = list(DatasetFile.iterator(DatasetFile.select().where(DatasetFile.id << file_ids)))
    for f in files:
        claim_args_true(1431, f.user_id == user_id and not f.parent and (not f.dataset or f.dataset == dataset))

    dataset = dataset.update_dataset(title, description, license, len(files))
    for f in DatasetFile.iterator(dataset.datasetfile_set):
        f.dataset = None
        f.save()
    for f in files:
        f.dataset = dataset
        f.save()
    data = {
        'dataset': dataset.to_dict(g.fields)
    }
    return api_success_response(data)


@bp_api.route('/datasets/<int:dataset_id>/hidden/', methods=['PUT'])
def update_dataset_hidden(dataset_id):
    """
    更新数据集是否隐藏
    :param dataset_id: 
    :return: 
    """
    user_id, hidden = map(g.json.get, ('user_id', 'hidden'))
    dataset = Dataset.query_by_id(dataset_id)
    claim_args_true(1104, dataset)
    claim_args(1401, user_id, hidden)
    claim_args_int(1402, user_id)
    claim_args_bool(1402, hidden)
    claim_args_true(1103, dataset.user_id == user_id)

    dataset.hidden = hidden
    dataset.save()
    data = {
        'dataset': dataset.to_dict(g.fields)
    }
    return api_success_response(data)


@bp_api.route('/datasets/<int:dataset_id>/total_notebooks/', methods=['PUT'])
def update_dataset_total_notebooks(dataset_id):
    """
    更新数据集的笔记个数
    :param dataset_id: 
    :return: 
    """
    delta = g.json.get('delta')
    dataset = Dataset.query_by_id(dataset_id)
    claim_args_true(1104, dataset)
    claim_args(1401, delta)
    claim_args_int(1402, delta)

    dataset.total_notebooks += delta
    dataset.save()
    data = {
        'dataset': dataset.to_dict(g.fields)
    }
    return api_success_response(data)


@bp_api.route('/datasets/<int:dataset_id>/total_topics/', methods=['PUT'])
def update_dataset_total_topics(dataset_id):
    """
    更新数据集的话题个数
    :param dataset_id: 
    :return: 
    """
    delta = g.json.get('delta')
    dataset = Dataset.query_by_id(dataset_id)
    claim_args_true(1104, dataset)
    claim_args(1401, delta)
    claim_args_int(1402, delta)

    dataset.total_topics += delta
    dataset.save()
    data = {
        'dataset': dataset.to_dict(g.fields)
    }
    return api_success_response(data)


@bp_api.route('/datasets/<int:dataset_id>/total_comments/', methods=['PUT'])
def update_dataset_total_comments(dataset_id):
    """
    更新数据集的评论个数
    :param dataset_id: 
    :return: 
    """
    delta = g.json.get('delta')
    dataset = Dataset.query_by_id(dataset_id)
    claim_args_true(1104, dataset)
    claim_args(1401, delta)
    claim_args_int(1402, delta)

    dataset.total_comments += delta
    dataset.save()
    data = {
        'dataset': dataset.to_dict(g.fields)
    }
    return api_success_response(data)


@bp_api.route('/datasets/<int:dataset_id>/total_votes/', methods=['PUT'])
def update_dataset_total_votes(dataset_id):
    """
    更新数据集的点赞个数
    :param dataset_id: 
    :return: 
    """
    delta = g.json.get('delta')
    dataset = Dataset.query_by_id(dataset_id)
    claim_args_true(1104, dataset)
    claim_args(1401, delta)
    claim_args_int(1402, delta)

    dataset.total_votes += delta
    dataset.save()
    data = {
        'dataset': dataset.to_dict(g.fields)
    }
    return api_success_response(data)


