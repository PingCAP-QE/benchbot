import typing

import pymysql.cursors


def cluster_version(tidb_host: str, tidb_port: str) -> typing.Mapping[str, typing.Any]:
    connection = pymysql.connect(host=tidb_host,
                                 port=int(tidb_port),
                                 user='root',
                                 password='',
                                 db='INFORMATION_SCHEMA',
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    version_info = dict()
    with connection.cursor() as cursor:
        sql = "SELECT `TYPE`, `VERSION`, `GIT_HASH` FROM `CLUSTER_INFO`"
        cursor.execute(sql)
        rows = cursor.fetchall()
    for row in rows:
        version_info[row["TYPE"]] = dict({
            "version": row["VERSION"],
            "git_hash": row["GIT_HASH"]
        })
    return version_info
