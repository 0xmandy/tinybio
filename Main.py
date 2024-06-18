import asyncio
import py_nillion_client as nillion
import os
import sys
import pytest

from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from helpers.nillion_client_helper import create_nillion_client
from helpers.nillion_keypath_helper import getUserKeyFromFile, getNodeKeyFromFile

load_dotenv()

async def main():
    cluster_id = os.getenv("NILLION_CLUSTER_ID")
    userkey = getUserKeyFromFile(os.getenv("NILLION_USERKEY_PATH_PARTY_1"))
    nodekey = getNodeKeyFromFile(os.getenv("NILLION_NODEKEY_PATH_PARTY_1"))

    client = create_nillion_client(userkey, nodekey)

    party_id = client.party_id
    user_id = client.user_id

    program_name="face_point_comparison"
    program_mir_path=f"../../programs-compiled/{program_name}.nada.bin"
    action_id = await client.store_program(
        cluster_id, program_name, program_mir_path
    )
    program_id=f"{user_id}/{program_name}"
    print('Stored program. action_id:', action_id)
    print('Stored program_id:', program_id)

    face_points1 = [nillion.SecretInteger(i) for i in range(68)]
    new_secret = nillion.Secrets({f"point1_{i}": face_points1[i] for i in range(68)})

    secret_bindings = nillion.ProgramBindings(program_id)
    secret_bindings.add_input_party("Party1", party_id)

    store_id = await client.store_secrets(
        cluster_id, secret_bindings, new_secret, None
    )
    print(f"Computing using program {program_id}")
    print(f"Use secret store_id: {store_id}")

    compute_bindings = nillion.ProgramBindings(program_id)
    compute_bindings.add_input_party("Party1", party_id)
    compute_bindings.add_output_party("Party1", party_id)

    face_points2 = [nillion.SecretInteger(i + 2) for i in range(68)]
    computation_time_secrets = nillion.Secrets({f"point2_{i}": face_points2[i] for i in range(68)})
    
    compute_id = await client.compute(
        cluster_id,
        compute_bindings,
        [store_id],
        computation_time_secrets,
        nillion.PublicVariables({}),
    )

    print(f"The computation was sent to the network. compute_id: {compute_id}")
    while True:
        compute_event = await client.next_compute_event()
        if isinstance(compute_event, nillion.ComputeFinishedEvent):
            print(f"✅  Compute complete for compute_id {compute_event.uuid}")
            print(f"🖥️  The result is {compute_event.result.value}")
            return compute_event.result.value
    
if __name__ == "__main__":
    asyncio.run(main())

@pytest.mark.asyncio
async def test_main():
    result = await main()
    assert result == {'is_same_person': False}  
