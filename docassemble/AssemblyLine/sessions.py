from collections.abc import Iterable
from typing import List, Dict, Any, Optional, Set, Union, Optional
from docassemble.base.util import (
    DAFile,
    DAFileCollection,
    DAFileList,
    get_session_variables,
    set_session_variables,
    set_variables,
    all_variables,
    user_info,
    variables_snapshot_connection,
    word,
    user_has_privilege,
    log,
    interview_url,
    action_button_html,
    url_action,
    url_ask,
    as_datetime,
    create_session,
    set_parts,
    user_logged_in,
    validation_error,
    format_time,
    interview_menu,
)
from docassemble.webapp.users.models import UserModel
from docassemble.webapp.db_object import init_sqlalchemy
from sqlalchemy.sql import text
from docassemble.base.functions import server, safe_json, serializable_dict
from .al_document import (
    ALDocument,
    ALDocumentBundle,
    ALStaticDocument,
    ALExhibit,
    ALExhibitList,
)
import json
import os

__all__ = [
    "is_file_like",
    "set_interview_metadata",
    "get_interview_metadata",
    "rename_interview_answers",
    "save_interview_answers",
    "get_filtered_session_variables",
    "load_interview_answers",
    "get_saved_interview_list",
    "interview_list_html",
    "get_filtered_session_variables_string",
    "load_interview_json",
    "export_interview_variables",
    "is_valid_json",
    "session_list_html",
]

db = init_sqlalchemy()

al_sessions_variables_to_remove: Set = {
    # Internal fields
    "_internal",
    "nav",
    "url_args",
    "device_local",
    "allow_cron",
    "feedback_form",
    "github_repo_name",
    "github_user",
    "interview_short_title",
    "metadata_title",
    "multi_user",
    "session_local",
    "speak_text",
    "user_local",
    # Database-like fields we don't need to copy
    "all_courts",
    "macourts",
    "court_emails",
    # AssemblyLine form-specific fields
    "al_form_type",
    "al_version",
    "form_approved_for_email_filing",
    "interview_metadata",
    "package_name",
    "package_version_number",
    "user_has_saved_answers",
    # Variables that should be calculated fresh
    "signature_date",
    "al_court_bundle",
    "al_user_bundle",
    "case_name",
    "al_logo",
    "AL_ORGANIZATION_HOMEPAGE",
    "AL_DEFAULT_STATE",
    "AL_DEFAULT_COUNTRY",
    "AL_DEFAULT_LANGUAGE",
    "AL_DEFAULT_OVERFLOW_MESSAGE",
    "AL_ORGANIZATION_TITLE",
    "about_this_interview_version_info",
    # Variables from saving/loading state
    "al_formatted_sessions",
    "al_sessions_copy_success",
    "al_sessions_fast_forward_filtered_vars",
    "al_sessions_fast_forward_session",
    "al_sessions_filtered_vars",
    "al_sessions_launch_new_session",
    "al_sessions_list",
    "al_sessions_new_session_id",
    "al_sessions_preview_variables",
    "al_sessions_save_session_snapshot",
    "al_sessions_save_session_snapshot_success",
    "al_sessions_snapshot_label",
    "al_sessions_snapshot_results",
    "al_sessions_source_session",
    "al_sessions_variables_to_remove",
    "al_simple_filtered_vars",
    "filtered_vars_tmp",
    "simple_filtered_vars_tmp",
    "al_sessions_url_ask_snapshot",
    "al_sessions_url_ask_fast_forward",
    "al_sessions_variables_to_remove_from_new_interview",
    "is_file_like",
    # Some type annotations from Typing that seem plausible we'll use (not everything)
    "Any",
    "Callable",
    "Dict",
    "Generic",
    "Iterable",
    "List",
    "Optional",
    "Set",
    "Tuple",
    "TypeVar",
    "Union",
    "Concatenate",
    "TypeLiteral",
    "ClassVar",
    "Final",
    "Annotated",
    "TypeGuard",
    "ParamSpec",
    "AnyStr",
    "Protocol",
    "NamedTuple",
    "NewType",
    "TypedDict",
    "FrozenSet",
    "DefaultDict",
    "OrderedDict",
    "ChainMap",
    "Counter",
    "Deque",
    "IO",
    "TextIO",
    "BinaryIO",
    "Pattern",
    "Match",
    "Text",
    # Variables that should always be created by code, so safe to recalculate
    "user_started_case",
    "user_role",
    "menu_items",
    "al_menu_items",
}

al_sessions_variables_to_remove_from_new_interview = [
    "docket_number",
    "docket_numbers",
    "user_ask_role",
]

system_interviews:List[Dict[str, Any]] = interview_menu()


def _package_name(package_name: str = None):
    """Get package name without the name of the current module, like: docassemble.ALWeaver instead of
    docassemble.ALWeaver.advertise_capabilities"""
    if not package_name:
        package_name = __name__
    try:
        return ".".join(package_name.split(".")[:-1])
    except:
        return package_name


al_session_store_default_filename = f"{_package_name()}:al_saved_sessions_store.yml"


def is_file_like(obj):
    return isinstance(
        obj,
        (
            DAFile,
            DAFileCollection,
            DAFileList,
            ALDocument,
            ALDocumentBundle,
            ALStaticDocument,
            ALExhibit,
            ALExhibitList,
        ),
    )


def set_interview_metadata(
    filename: str, session_id: int, data: Dict, metadata_key_name="metadata"
) -> None:
    """Add searchable interview metadata for the specified filename and session ID.
    Intended to be used to add an interview title, etc.
    Standardized metadata dictionary:
    - title
    - subtitle
    - original_interview_filename
    - variable_count
    """
    server.write_answer_json(
        session_id, filename, safe_json(data), tags=metadata_key_name, persistent=True
    )


def get_interview_metadata(
    filename: str, session_id: int, metadata_key_name: str = "metadata"
) -> Dict:
    """Retrieve the unencrypted metadata associated with an interview.
    We implement this with the docassemble jsonstorage table and a dedicated `tag` which defaults to `metadata`.
    """
    conn = variables_snapshot_connection()
    with conn.cursor() as cur:
        query = "select data from jsonstorage where filename=%(filename)s and tags=%(tags)s and key=%(session_id)s"
        cur.execute(
            query,
            {"filename": filename, "tags": metadata_key_name, "session_id": session_id},
        )
        val = cur.fetchone()
    conn.close()
    if val and len(val):
        return val[0]  # cur.fetchone() returns a tuple
    return val or {}


def get_saved_interview_list(
    filename: Optional[str] = al_session_store_default_filename,
    user_id: Union[int, str] = None,
    metadata_key_name: str = "metadata",
    limit:int = 50,
    offset:int = 0,
    filename_to_exclude: str = "",
    exclude_current_filename: bool = True,
) -> List[Dict]:
    """Get a list of saved sessions for the specified filename. If the save_interview_answers function was used
    to add metadata, the result list will include columns containing the metadata.
    If the user is a developer or administrator, setting user_id = None will list all interviews on the server. Otherwise,
    the user is limited to their own sessions.
    """
    # We use an `offset` instead of a cursor because it is simpler and clearer
    # while it appears to be performant enough for real-world usage.
    # Up to ~ 1,000 sessions performs well and is higher than expected for an end-user
    get_sessions_query = text(
        """
           SELECT  userdict.indexno
           ,userdict.filename as filename
           ,num_keys
           ,userdictkeys.user_id as user_id
           ,userdict.modtime as modtime
           ,userdict.key as key
           ,jsonstorage.data->'title' as title
           ,jsonstorage.data->'description' as description
           ,jsonstorage.data->'steps' as steps
           ,jsonstorage.data->'original_interview_filename' as original_interview_filename
           ,jsonstorage.data->'answer_count' as answer_count
           ,jsonstorage.data as data
    FROM userdict 
    NATURAL JOIN 
    (
      SELECT  key
             ,MAX(modtime) AS modtime
             ,COUNT(key)   AS num_keys
      FROM userdict
      GROUP BY  key
    ) mostrecent
    LEFT JOIN userdictkeys
    ON userdictkeys.key = userdict.key
    LEFT JOIN jsonstorage
    ON userdict.key = jsonstorage.key AND (jsonstorage.tags = :metadata)
    WHERE (userdictkeys.user_id = :user_id or :user_id is null)
    
    AND
    (userdict.filename = :filename OR :filename is null)
    AND userdict.filename != :filename_to_exclude
    AND userdict.filename != :current_filename
    ORDER BY modtime desc 
    LIMIT :limit
    OFFSET :offset;
    """
    )

    if offset < 0:
        offset = 0

    if not filename:
        filename = None  # Explicitly treat empty string as equivalent to None
    if exclude_current_filename:
        current_filename = user_info().filename        
    else:
        current_filename = ""
    if not filename_to_exclude:
        filename_to_exclude = ""
    if user_id is None:
        if user_logged_in():
            user_id = user_info().id
        else:
            log("Asked to get interview list for user that is not logged in")
            return []

    if user_id == "all":
        if user_has_privilege(["developer", "admin"]):
            user_id = None
        elif user_logged_in():
            user_id = user_info().id
            log(
                f"User {user_info().email} does not have permission to list interview sessions belonging to other users"
            )
        else:
            log("Asked to get interview list for user that is not logged in")
            return []

    with db.connect() as con:
        rs = con.execute(
            get_sessions_query,
            metadata=metadata_key_name,
            user_id=user_id,
            filename=filename,
            limit=limit,
            offset=offset,
            filename_to_exclude=filename_to_exclude,
            current_filename=current_filename,
        )
    sessions = []
    for session in rs:
        sessions.append(session)

    return sessions


def interview_list_html(
    filename: str = al_session_store_default_filename,
    user_id: Union[int, str] = None,
    metadata_key_name: str = "metadata",
    # name_label: str = word("Title"),
    date_label: str = word("Date"),
    details_label: str = word("Details"),
    actions_label: str = word("Actions"),
    delete_label: str = word("Delete"),
    view_label: str = word("View"),
    load_action: str = "al_sessions_fast_forward_session",
    delete_action: str = "al_sessions_delete_session",
    view_only: bool = False,
    limit:int = 50,
    offset:int = 0,
) -> str:
    """Return a string containing an HTML-formatted table with the list of saved answers
    associated with the specified filename.

    Designed to return a list of "answer sets" and by default clicking a title will
    trigger an action to load the answers into the current session. This only works as
    designed when inside an AssemblyLine line interview.
    """
    # TODO: Currently, using the `word()` function for translation, but templates
    # might be more flexible
    answers = get_saved_interview_list(
        filename=filename,
        user_id=user_id,
        metadata_key_name=metadata_key_name,
        limit=limit,
        offset=offset,
        exclude_current_filename=False,        
    )

    if not answers:
        return ""

    table = '<div class="table-responsive"><table class="table table-striped al-saved-answer-table">'
    table += f"""
    <thead>
      <th scope="col">
        &nbsp;
      </th>
      <th scope="col">{ date_label }</th>
      <th scope="col">{ details_label }</th>
      <th scope="col">{ actions_label }</th>
      </th>
    </thead>
    <tbody>
"""

    for answer in answers:
        answer = dict(answer)
        # Never display the current interview session
        if answer.get("key") == user_info().session:
            continue
        table += """<tr class="al-saved-answer-table-row">"""
        if view_only:
            table += f"""
            <td>{ nice_interview_title(answer) }</td>
            """
        else:
            table += f"""
            <td><a href="{ url_action(load_action, i=answer.get("filename"), session=answer.get("key")) }"><i class="fa fa-regular fa-folder-open" aria-hidden="true"></i>&nbsp;{answer.get("title") or answer.get("filename","").replace(":", " ") or "Untitled interview" }</a></td>
            """
        table += f"""
        <td>{ as_datetime(answer.get("modtime")) }</td>
        <td>Page { answer.get("steps") or answer.get("num_keys") } <br/>
            {answer.get("original_interview_filename") or answer.get("filename") or "" }
        </td>
        <td>
          <a href="{ url_action(delete_action, filename=answer.get("filename"), session=answer.get("key")) }"><i class="far fa-trash-alt" title="{ delete_label }" aria-hidden="true"></i><span class="sr-only">{ delete_label }</span></a>
          <a target="_blank" href="{ interview_url(i=answer.get("filename"), session=answer.get("key")) }">
              <i class="far fa-eye" aria-hidden="true" title="{ view_label }"></i>
              <span class="sr-only">{ view_label }</span>
          </a>
        </td>
        """
        table += "</tr>"
    table += "</tbody></table></div>"

    return table


def nice_interview_title(
    answer: Dict[str, str],
    use_metadata: bool = True,
) -> str:
    """
    Return a human readable version of the interview name. Will try several strategies
    in descending priority order.
    1. If the "title" metadata is set, use that
    2. If no "title" metadata, try looking up the interview title from the `dispatch` directive
    3. Try removing the package and path from the filename and replace _ with spaces.
    4. Finally, return "Untitled interview" or translated phrase from system-wide words.yml
    """
    if use_metadata and answer.get("title"):
        return answer.get("title","")    
    if answer.get("filename"):
        for interview in system_interviews:
            if answer.get("filename") == interview.get("filename"):
                return interview.get("title")
        filename = os.path.splitext(os.path.basename(answer.get("filename","")))[0]
        if ":" in filename:
            filename = filename.split(":")[1]
        return filename.replace("_", " ").capitalize()
    else:
        return word("Untitled interview")


def session_list_html(
    filename: Optional[str] = None,
    user_id: Union[int, str] = None,
    metadata_key_name: str = "metadata",
    filename_to_exclude: str = al_session_store_default_filename,
    exclude_current_filename:bool = True,
    # name_label: str = word("Title"),
    date_label: str = word("Date"),
    details_label: str = word("Details"),
    actions_label: str = word("Actions"),
    delete_label: str = word("Delete"),
    rename_label: str = word("Rename"),
    delete_action: str = "interview_list_delete_session",
    copy_action: str = "interview_list_copy_action",
    clone_label: str = word("Copy as answer set"),
    limit:int = 50,
    offset:int = 0,    
) -> str:
    """Return a string containing an HTML-formatted table with the list of user sessions.
    While interview_list_html() is for answer sets, this feature is for standard
    user sessions. The results exclude the answer set filename by default.
    """

    # TODO: think through how to translate this function. Templates probably work best but aren't
    # convenient to pass around
    answers = get_saved_interview_list(
        filename=filename,
        user_id=user_id,
        metadata_key_name=metadata_key_name,
        limit=limit,
        offset=offset,
        filename_to_exclude=filename_to_exclude,
        exclude_current_filename=exclude_current_filename,
    )

    if not answers:
        return ""

    table = '<div class="table-responsive"><table class="table table-striped al-saved-answer-table">'
    table += f"""
    <thead>
      <th scope="col">
        &nbsp;
      </th>
      <th scope="col">{ date_label }</th>
      <th scope="col">{ details_label }</th>
      <th scope="col">{ actions_label }</th>
      </th>
    </thead>
    <tbody>
"""

    for answer in answers:
        answer = dict(answer)
        # Never display the current interview session
        if answer.get("key") == user_info().session:
            continue
        table += """<tr class="al-saved-answer-table-row">"""
        table += f"""
        <td><a href="{ interview_url(i=answer.get("filename"), session=answer.get("key")) }"><i class="fa fa-regular fa-folder-open" aria-hidden="true"></i>&nbsp;{ nice_interview_title(answer) }</a></td>
        """
        table += f"""
        <td>{ as_datetime(answer.get("modtime")) } <br/>
            { format_time(as_datetime(answer.get("modtime")).time(), format="h:mm a") }
        </td>
        <td>Page { answer.get("steps") or answer.get("num_keys") }
        </td>
        <td>
          <a href="{ interview_url(i=answer.get("filename"), session=answer.get("key")) }"><i class="fa-solid fa-i-cursor" aria-hidden="true" title="{ rename_label }"></i><span class="sr-only">{ rename_label }</span></a>
          &nbsp;
          <a href="{ url_action(copy_action) }"><i class="fa-regular fa-clone" aria-hidden="true" title="{clone_label}"></i><span class="sr-only">{ clone_label }</span></a>
          &nbsp;
          <a href="{ url_action(delete_action, filename=answer.get("filename"), session=answer.get("key")) }"><i class="far fa-trash-alt" title="{ delete_label }" aria-hidden="true"></i><span class="sr-only">{ delete_label }</span></a>
        </td>
        """
        table += "</tr>"
    table += "</tbody></table></div>"

    return table

def rename_interview_answers(
    filename: str,
    session_id: int,
    new_name: str,
    metadata_key_name: str = "metadata",
) -> None:
    """Update the 'title' metadata of an interview, as stored in the dedicated `metadata` column, without touching other
    metadata that may be present."""
    existing_metadata = get_interview_metadata(
        filename, session_id, metadata_key_name=metadata_key_name
    )
    existing_metadata["title"] = new_name
    set_interview_metadata(
        filename, session_id, existing_metadata, metadata_key_name=metadata_key_name
    )
    if session_id == user_info().session:
        set_parts(subtitle=new_name)
    else:
        try:
            set_session_variables(
                filename,
                session_id,
                {"_internal['subtitle']": new_name},
                overwrite=True,
            )
        except:
            log(
                f"Unable to update internal interview subtitle for session {filename}:{session_id} with new name {new_name}"
            )


def set_current_session_metadata(
    data: Dict[str, Any],
    metadata_key_name: str = "metadata",
) -> None:
    """
    Set metadata for the current session, such as the title, in an unencrypted database entry.
    This may be helpful for faster SQL queries and reports, such as listing interview answers.
    """
    return set_interview_metadata(
        user_info().filename,
        user_info().session,
        data,
        metadata_key_name=metadata_key_name,
    )


def rename_current_session(
    new_name: str,
    metadata_key_name: str = "metadata",
) -> None:
    """Update the "title" metadata entry for the current session without changing any other
    metadata that might be present."""
    return rename_interview_answers(
        user_info().filename,
        user_info().session,
        new_name,
        metadata_key_name=metadata_key_name,
    )


def save_interview_answers(
    filename: str = al_session_store_default_filename,
    variables_to_filter: Iterable = None,
    metadata: Dict = None,
    metadata_key_name: str = "metadata",
) -> str:
    """Copy the answers from the running session into a new session with the given
    interview filename."""
    # Avoid using mutable default parameter
    if not variables_to_filter:
        variables_to_filter = al_sessions_variables_to_remove
    if not metadata:
        metadata = {}

    # Get variables from the current session
    all_vars = all_variables(simplify=False)

    all_vars = {
        item: all_vars[item]
        for item in all_vars
        if not item in variables_to_filter and not is_file_like(all_vars[item])
    }

    try:
        # Sometimes include_internal breaks things
        metadata["steps"] = (
            all_variables(include_internal=True).get("_internal").get("steps", -1)
        )
    except:
        metadata["steps"] = -1

    metadata["original_interview_filename"] = all_variables(special="metadata").get(
        "title", user_info().filename.replace(":", " ").replace(".", " ")
    )
    metadata["answer_count"] = len(all_vars)

    # Create a new session
    new_session_id = create_session(filename)

    # Copy in the variables from this session
    set_session_variables(filename, new_session_id, all_vars, overwrite=True)

    # Add the metadata
    set_interview_metadata(filename, new_session_id, metadata)
    # Make the title display as the subtitle on the "My interviews" page
    if metadata.get("title"):
        try:
            set_session_variables(
                filename,
                new_session_id,
                {"_internal['subtitle']": metadata.get("title")},
                overwrite=True,
            )
        except:
            log(
                f"Unable to set internal interview subtitle for session {filename}:{new_session_id} with name {metadata.get('title')}"
            )

    return new_session_id


def get_filtered_session_variables(
    filename: Optional[str] = None,
    session_id: Optional[int] = None,
    variables_to_filter: Optional[Union[Set[str], List[str]]] = None,
) -> Dict[str, Any]:
    """
    Get a filtered subset of the variables from the specified interview filename and session.

    If no filename and session ID are specified, return filtered list of variables from the current interview.
    """
    if not variables_to_filter:
        variables_to_filter = al_sessions_variables_to_remove

    if filename and session_id:
        all_vars = get_session_variables(filename, session_id, simplify=False)
    else:
        all_vars = all_variables(simplify=False)

    # Remove items that we were explicitly told to remove
    # Delete all files and ALDocuments
    return {
        item: all_vars[item]
        for item in all_vars
        if not item in variables_to_filter and not is_file_like(all_vars[item])
    }


def get_filtered_session_variables_string(
    filename: Optional[str] = None,
    session_id: Optional[int] = None,
    variables_to_filter: Optional[Union[Set[str], List[str]]] = None,
) -> str:
    """
    Get a JSON string representing the filtered contents of the specified filename and session_id. If no filename and session_id
    are provided, the output will contain the variables from the current session.
    """
    simple_vars = serializable_dict(
        get_filtered_session_variables(filename, session_id, variables_to_filter)
    )
    return json.dumps(simple_vars)


def load_interview_answers(
    old_interview_filename: str,
    old_session_id: int,
    new_session: bool = False,
    new_interview_filename: str = None,
    variables_to_filter: List[str] = None,
) -> Optional[int]:
    """
    Load answers from the specified session. If the parameter new_session = True, create a new session of
    the specified or current interview filename. Otherwise, load the answers into the active session.
    Returns the ID of the newly created session
    Create a new session with the variables from the specified session ID. Returns the ID of the newly
    created and "filled" session.
    """
    old_variables = get_filtered_session_variables(
        old_interview_filename, old_session_id, variables_to_filter
    )

    if new_session:
        if not new_interview_filename:
            new_interview_filename = user_info().filename
        new_session_id = create_session(new_interview_filename)
        set_session_variables(new_interview_filename, new_session_id, old_variables)
        return new_session_id
    else:
        try:
            set_variables(old_variables)
            return True
        except:
            return False


def load_interview_json(
    json_string: str,
    new_session: bool = False,
    new_interview_filename: str = None,
    variables_to_filter: List[str] = None,
) -> Optional[int]:
    """
    Provided a JSON string, load the specified variables into a Docassemble session. JSON with annotated class names
    will be processed into Docassemble objects.

    If new_session is not provided, the JSON answers will be loaded into the current interview.
    """
    json_processed = json.loads(json_string)

    if new_session:
        if not new_interview_filename:
            new_interview_filename = user_info().filename
        new_session_id = create_session(new_interview_filename)
        set_session_variables(
            new_interview_filename, new_session_id, json_processed, process_objects=True
        )
        return new_session_id
    else:
        try:
            set_variables(json_processed, process_objects=True)
            return True
        except:
            return False


def export_interview_variables(
    filename: Optional[str] = None,
    session_id: Optional[int] = None,
    variables_to_filter: Union[Set, List[str]] = None,
    output: DAFile = None,
) -> DAFile:
    """
    Get a DAFile with the JSON representation of the specified session's interview answers. The output is compatible with
    set_session_variables(process_objects=True) and set_variables(process_objects=True)
    """
    if not output:
        output = DAFile()
    output.initialize(filename="variables.json")
    variables_string = get_filtered_session_variables_string(
        filename,
        session_id,
        variables_to_filter,
    )

    output.write(variables_string)
    output.commit()
    return output


def is_valid_json(json_string: str) -> bool:
    try:
        json.loads(json_string)
    except:
        validation_error("Enter a valid JSON-formatted string")
        return False
    return True
