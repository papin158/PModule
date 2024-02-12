import cython

cpdef bint is_admin(str state, set all_states):
    cdef str state_prefix = state.split(":")[0]
    return state_prefix in all_states