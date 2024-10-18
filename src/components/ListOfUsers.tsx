import React, { useEffect, useState } from "react";
import { CoopApi, TapirUser } from "../api-client";
import { useApi } from "../hooks/useApi.ts";

interface ListOfUsersProps {}

const ListOfUsers: React.FC<ListOfUsersProps> = () => {
  const api = useApi(CoopApi);
  const [users, setUsers] = useState<TapirUser[]>([]);

  useEffect(() => {
    fetchUsers();
  }, []);

  function fetchUsers() {
    api
      .coopApiTapirUsersList({ limit: 10, offset: 0 })
      .then((users) => {
        setUsers(users.results);
      })
      .catch((error) => {
        console.error("THERE IS AN ERROR");
        console.error(error);
      });
  }

  return (
    <>
      <ul>
        {users.map((user: TapirUser) => (
          <li key={user.id}>{user.username}</li>
        ))}
      </ul>
    </>
  );
};

export default ListOfUsers;
