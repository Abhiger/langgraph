from langgraph.checkpoint.base import ChannelVersions
from langgraph.constants import CHECKPOINT_NAMESPACE_SEPARATOR
from langgraph.pregel.types import StateSnapshot


def get_new_channel_versions(
    previous_versions: ChannelVersions, current_versions: ChannelVersions
) -> ChannelVersions:
    """Get new channel versions."""
    if previous_versions:
        version_type = type(next(iter(current_versions.values()), None))
        null_version = version_type()
        new_versions = {
            k: v
            for k, v in current_versions.items()
            if v > previous_versions.get(k, null_version)
        }
    else:
        new_versions = current_versions

    return new_versions


def assemble_state_snapshot_hierarchy(
    root_checkpoint_ns: str,
    checkpoint_ns_to_state_snapshots: dict[str, StateSnapshot],
) -> StateSnapshot:
    checkpoint_ns_list_to_visit = sorted(
        checkpoint_ns_to_state_snapshots.keys(),
        key=lambda x: len(x.split(CHECKPOINT_NAMESPACE_SEPARATOR)),
    )
    while checkpoint_ns_list_to_visit:
        checkpoint_ns = checkpoint_ns_list_to_visit.pop()
        state_snapshot = checkpoint_ns_to_state_snapshots[checkpoint_ns]
        *path, subgraph_node = checkpoint_ns.split(CHECKPOINT_NAMESPACE_SEPARATOR)
        parent_checkpoint_ns = CHECKPOINT_NAMESPACE_SEPARATOR.join(path)
        if subgraph_node and (
            parent_state_snapshot := checkpoint_ns_to_state_snapshots.get(
                parent_checkpoint_ns
            )
        ):
            parent_subgraph_snapshots = {
                **(parent_state_snapshot.subgraph_state_snapshots or {}),
                subgraph_node: state_snapshot,
            }
            checkpoint_ns_to_state_snapshots[
                parent_checkpoint_ns
            ] = checkpoint_ns_to_state_snapshots[parent_checkpoint_ns]._replace(
                subgraph_state_snapshots=parent_subgraph_snapshots
            )

    state_snapshot = checkpoint_ns_to_state_snapshots.pop(root_checkpoint_ns, None)
    if state_snapshot is None:
        raise ValueError(f"Missing checkpoint for checkpoint NS '{root_checkpoint_ns}'")
    return state_snapshot
