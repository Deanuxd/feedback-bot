from discord import Member

DEV_ROLES = ["Developer", "Dev"]
MOD_ROLES = ["Moderator", "Mod", "Admin"]

def has_role(member: Member, role_names: list[str]) -> bool:
    return any(role.name.lower() in [r.lower() for r in role_names] for role in member.roles)

def is_dev(member: Member) -> bool:
    return has_role(member, DEV_ROLES)

def is_mod(member: Member) -> bool:
    return member.guild_permissions.manage_messages or has_role(member, MOD_ROLES)

def is_owner(member: Member) -> bool:
    """Check if the member is the server owner."""
    return member.guild.owner_id == member.id

def is_privileged(member: Member) -> bool:
    """Check if member has privileged access (Dev, Mod, or Owner)."""
    return is_dev(member) or is_mod(member) or is_owner(member)

def can_manage_threads(member: Member) -> bool:
    """Check if member can manage threads (Dev, Mod, or Owner)."""
    return is_privileged(member)
