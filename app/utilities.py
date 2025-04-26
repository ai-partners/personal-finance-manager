class Utilities:

    def authenticate_user(self, username: str, password: str) -> tuple[str, dict]:
        # Emulate a user authentication process
        if (username, password) == ("daniel", "admin"):
            identifier="Daniel"
            metadata={"UserId": "1", "provider": "credentials"}
            return identifier, metadata

        if (username, password) == ("andres", "admin"):
            
            identifier="Andrés"
            metadata={"UserId": "2", "provider": "credentials"}
            return identifier, metadata

        else:
            return None