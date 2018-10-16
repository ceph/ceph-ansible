#!/bin/bash

create_snapshots() {
  local pattern=$1
  for vm in $(sudo virsh list --all | awk "/${pattern}/{print \$2}"); do
    sudo virsh shutdown "${vm}"
    wait_for_shutoff "${vm}"
    sudo virsh snapshot-create "${vm}"
    sudo virsh start "${vm}"
  done
}

delete_snapshots() {
  local pattern=$1
  for vm in $(sudo virsh list --all | awk "/${pattern}/{print \$2}"); do
    for snapshot in $(sudo virsh snapshot-list "${vm}" --name); do
      echo "deleting snapshot ${snapshot} (vm: ${vm})"
      sudo virsh snapshot-delete "${vm}" "${snapshot}"
    done
  done
}

revert_snapshots() {
  local pattern=$1
  for vm in $(sudo virsh list --all | awk "/${pattern}/{print \$2}"); do
    echo "restoring last snapshot for ${vm}"
    sudo virsh snapshot-revert "${vm}" --current
    sudo virsh start "${vm}"
  done
}

wait_for_shutoff() {
  local vm=$1
  local retries=60
  local delay=2

  until test "${retries}" -eq 0
  do
    echo "waiting for ${vm} to be shut off... #${retries}"
    sleep "${delay}"
    let "retries=$retries-1"
    local current_state=$(sudo virsh domstate "${vm}")
    test "${current_state}" == "shut off" && return
  done
  echo couldnt shutoff "${vm}"
  exit 1
}

while :; do
    case $1 in
        -d|--delete)
            delete_snapshots "$2"
            exit
            ;;
        -i|--interactive)
            INTERACTIVE=TRUE
            ;;
        -s|--snapshot)
            create_snapshots "$2"
            ;;
        -r|--revert)
            revert_snapshots "$2"
            ;;
        --)
            shift
            break
            ;;
        *)
            break
    esac

    shift
done
