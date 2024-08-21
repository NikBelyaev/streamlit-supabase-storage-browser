import contextlib
import copy
import fnmatch
import os
import os.path
import urllib
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Optional, TypedDict
from urllib.parse import urljoin

import numpy as np
import requests
import streamlit as st
import streamlit.components.v1 as components
from filetype import audio_match, image_match, video_match
from storage3.utils import SyncClient
from streamlit_ace import st_ace
from streamlit_embeded import st_embeded

CACHE_FILE_NAME = ".st-tree.cache"

parent_dir = os.path.dirname(os.path.abspath(__file__))
build_dir = os.path.join(parent_dir, "frontend/build")
_component_func = components.declare_component(
    "streamlit_supabase_storage_browser", path=build_dir
)


class File(TypedDict):
    path: Path
    size: float  # bytes
    create_time: float  # timestamp
    update_time: float  # timestamp
    access_time: float  # timestamp


class Bucket:
    def __init__(
        self,
        supabase: SyncClient,
        bucket_id: str,
        path: Optional[Path] = None,
        *,
        extensions: Optional[tuple[str]] = None,
    ):
        self.__supabase = supabase
        self.__bucket_id = bucket_id
        self.__path = path

        self.__extensions = extensions or ()

    @property
    def public_url(self) -> str:
        return f'{self.__supabase.storage_url}/object/public/{self.__bucket_id}/'

    def list(
        self,
        glob_patterns: tuple[str] = ('*/**',),
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[dict] = None
    ) -> tuple[File]:
        def filter_func(file: File) -> bool:
            # TODO: Move to DB level
            return any(fnmatch.fnmatch(file['path'], pattern) for pattern in glob_patterns)

        query = self._query()

        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        if order_by:
            query = query.order_by(**order_by)

        raw_files = query.execute().data
        files = map(translate_storage_file, raw_files)

        return tuple(filter(filter_func, files))

    def exists(self, path: Path) -> bool:
        return bool(self._query().eq('name', path).maybe_single().execute())

    def _query(self):
        bucket = (
            self.__storage()
            .select('name, created_at, updated_at, last_accessed_at, metadata->size')
            .eq('bucket_id', self.__bucket_id)
        )
        if self.__path is not None:
            bucket = bucket.like('name', f'{self.__path}%')
        if self.__extensions:
            bucket = bucket.like_any_of('name', f'{",".join([f"%{extension}" for extension in self.__extensions])}')

        return bucket

    def __storage(self):
        return self.__supabase.schema('storage').table('objects')


def translate_storage_file(storage_file: dict) -> File:
    return File(
        path=storage_file['name'],
        size=storage_file['size'],
        access_time=datetime.fromisoformat(storage_file['last_accessed_at']).timestamp() / 1000,
        create_time=datetime.fromisoformat(storage_file['created_at']).timestamp() / 1000,
        update_time=datetime.fromisoformat(storage_file['updated_at']).timestamp() / 1000,
    )


def _do_code_preview(url, **kwargs):
    content = requests.get(url).text
    st.code(content, **kwargs)


def _do_pdf_preview(url, height="420px", **kwargs):
    safe_url = escape(url)
    pdf_display = f'<iframe src="{safe_url}" width="100%" min-height="240px" height="{height} type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


# def _do_molecule_preview(root, file_path, url, **kwargs):
#     use_auto = kwargs.pop("use_auto", False)
#     abs_path = os.path.join(root, file_path)
#     test_traj_path = os.path.splitext(abs_path)[0] + ".xtc"
#     if os.path.exists(test_traj_path):
#         traj_path = test_traj_path
#         traj_url = os.path.splitext(url)[0] + ".xtc" if url else None
#     else:
#         traj_path = None
#         traj_url = None
#     if use_auto:
#         st_molstar_auto(
#             [{"file": url, "local": abs_path} if url else abs_path], **kwargs
#         )
#     else:
#         if url:
#             st_molstar_remote(url, traj_url, **kwargs)
#         else:
#             st_molstar(abs_path, traj_path, **kwargs)
#     return True


def _do_csv_preview(url, **kwargs):
    import pandas as pd

    content = requests.get(url).text

    df = pd.read_csv(content)
    mask = df.applymap(type) != bool
    d = {True: "True", False: "False"}
    df = df.where(mask, df.replace(d))
    df = df.replace(np.nan, None)
    st.dataframe(df, **kwargs)


def _do_tsv_preview(url, **kwargs):
    import pandas as pd

    content = requests.get(url).text

    df = pd.read_table(content)
    mask = df.applymap(type) != bool
    d = {True: "True", False: "False"}
    df = df.where(mask, df.replace(d))
    df = df.replace(np.nan, None)
    st.dataframe(df, **kwargs)


def _do_json_preview(url, **kwargs):
    content = requests.get(url).json()
    st.json(content, **kwargs)


def _do_html_preview(url, **kwargs):
    html = requests.get(url).text
    st_embeded(html, **kwargs)


def _do_markdown_preview(url, **kwargs):
    md = requests.get(url).text
    st.markdown(md, unsafe_allow_html=True)


def _do_plain_preview(url, **kwargs):
    plain = requests.get(url).content
    key = f'{kwargs.get("key", url)}-preview'
    st_ace(value=plain, readonly=True, show_gutter=False, key=key)


# RNA Secondary Structure Formats
# DB (dot bracket) format (.db, .dbn) is a plain text format that can encode secondory structure.
def _do_dbn_preview(url, **kwargs):
    content = requests.get(url).text
    encoding = urllib.parse.urlencode(
        {"id": "fasta", "file": content}, safe=r"()[]{}>#"
    )
    encoding = encoding.replace("%0A", "%5Cn").replace("#", ">")
    url = r"https://mrna-proxy.mlops.dp.tech/forna/forna.html?" + encoding
    components.iframe(url, height=600)


PREVIEW_HANDLERS = {
    extention: handler
    for extentions, handler in [
        # (
        #     (
        #         ".pdb",
        #         ".pdbqt",
        #         ".ent",
        #         ".trr",
        #         ".nctraj",
        #         ".nc",
        #         ".ply",
        #         ".bcif",
        #         ".sdf",
        #         ".cif",
        #         ".mol",
        #         ".mol2",
        #         ".xyz",
        #         ".sd",
        #         ".gro",
        #         ".mrc",
        #     ),
        #     _do_molecule_preview,
        # ),
        # ((".mrc",), partial(_do_molecule_preview, use_auto=True)),
        ((".json",), _do_json_preview),
        ((".pdf",), _do_pdf_preview),
        ((".csv",), _do_csv_preview),
        ((".tsv",), _do_tsv_preview),
        ((".log", ".txt", ".md", ".upf", ".UPF", ".orb"), _do_plain_preview),
        ((".md",), _do_markdown_preview),
        ((".py", ".sh"), _do_code_preview),
        ((".html", ".htm"), _do_html_preview),
        ((".dbn",), _do_dbn_preview),
    ]
    for extention in extentions
}


def show_file_preview(
    target_path,
    artifacts_site,
    key=None,
    height=None,
    overide_preview_handles=None,
    **kwargs,
):
    preview, raw = st.container(), None

    with preview:
        url = urljoin(artifacts_site, target_path) if artifacts_site else None
        ext = os.path.splitext(target_path)[1]
        handles = copy.copy(PREVIEW_HANDLERS)
        handles.update(overide_preview_handles or {})
        if ext in handles:
            try:
                handler = handles[ext]
                handler(url, **kwargs)
            except Exception as e:
                st.error(f"failed preview {target_path}")
                st.exception(e)
        else:
            content = requests.get(url).content

            if image_match(content):
                st.image(content, **kwargs)
            elif ft := video_match(content):
                st.video(url, format=ft.mime, **kwargs)
            elif ft := audio_match(content):
                st.audio(content, format=ft.mime, **kwargs)
            else:
                st.info(f"No preview available for {ext}")

    # if raw:
    #     with raw:
    #         if requests.head(url).headers['content-length'] >= 100000:
    #                 st.warning("File too large, only show first 10000 lines")
    #             key = f"{kwargs.get('key', abs_path)}-raw"
    #             st_ace(value="".join(rs), readonly=True, show_gutter=False, key=key)


def st_supabase_storage_browser(
    supabase: SyncClient,
    bucket_id: str,
    path: Optional[Path] = None,
    *,
    show_preview=True,
    show_preview_top=False,
    glob_patterns=("**/*",),
    ignore_file_select_event=False,
    file_ignores=None,
    select_filetype_ignores=None,
    extentions=None,
    show_delete_file=False,
    show_choose_file=False,
    show_choose_folder=False,
    show_download_file=True,
    show_new_folder=False,
    show_upload_file=False,
    show_rename_file=False,
    show_rename_folder=False,
    limit=None,
    offset=None,
    key=None,
    use_cache=False,
    overide_preview_handles=None,
    sort=None,
):
    bucket = Bucket(supabase, bucket_id, path, extensions=extentions)

    files = bucket.list(glob_patterns,
                        limit=limit,
                        offset=offset,
                        order_by=sort)

    if show_preview and show_preview_top:
        preview = st.container()
    else:
        preview = contextlib.nullcontext()

    event = _component_func(
        files=files,
        show_choose_file=show_choose_file,
        show_choose_folder=show_choose_folder,
        show_download_file=show_download_file,
        show_upload_file=show_upload_file,
        show_delete_file=show_delete_file,
        show_new_folder=show_new_folder,
        show_rename_file=show_rename_file,
        show_rename_folder=show_rename_folder,
        ignore_file_select_event=ignore_file_select_event,
        artifacts_download_site=bucket.public_url,
        artifacts_site=bucket.public_url,
        key=key,
    )

    if (
        isinstance(event, dict)
        and event.get('type') == 'SELECT_FILE'
        and not any(event["target"]["path"].endswith(ft) for ft in select_filetype_ignores or [])
    ):
        file = event["target"]

        if not bucket.exists(file['path']):
            st.warning(f"File {file['path']} not found")
            return event

        if show_preview:
            with preview, st.expander("", expanded=True):
                show_file_preview(
                    file['path'],
                    bucket.public_url,
                    overide_preview_handles=overide_preview_handles,
                    key=f"{key}-preview"
                )

    return event
