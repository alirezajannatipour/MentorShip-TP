from fastapi import APIRouter, Response

from src.api.dependencies import CurrentUser, DbConn
from src.schemas.addresses import AddressCreate, AddressOut
from src.services import addresses as addresses_service

router = APIRouter(prefix="/addresses", tags=["addresses"])


@router.get("", response_model=list[AddressOut])
def list_addresses(user: CurrentUser, conn: DbConn):
    return addresses_service.list_addresses(conn, user)


@router.post("", status_code=201, response_model=AddressOut)
def create_address(payload: AddressCreate, user: CurrentUser, conn: DbConn):
    return addresses_service.create_address(conn, user, payload)


@router.delete("/{address_id}", status_code=204)
def delete_address(address_id: int, user: CurrentUser, conn: DbConn):
    addresses_service.delete_address(conn, user, address_id)
    return Response(status_code=204)
