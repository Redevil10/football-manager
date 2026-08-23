# services/__init__.py - Application services

"""Work that needs both business rules and stored data.

`core` holds things with no dependencies of their own -- configuration,
exception types, styles, small text helpers -- so anything that reaches for the
database does not belong there. `core.auth` did, which made `core` import `db`
while `db` imported `core`, a cycle in the layer graph.

Authentication, sessions and permission checks live here instead: above `db`,
below `routes` and `render`.
"""
