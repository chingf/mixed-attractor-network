import pdb
import numpy as np
from math import pi
import matplotlib.pyplot as plt

class RingNetwork(object):
    """
    A ring attractor network as described by Ben-Yishai & Sompolinsky (1994).

    In this model, one timestep corresponds to 100 ms. Wherever possible,
    variable notation corresponds with the notation used in the original paper.

    Args:
        N (int): Number of units in the network. Their preferred tuning evenly
           covers the ring
        K_inhib (float): Value of global inhibition

    Attributes:
        base_J0 (float): parameter representing uniform all-to-all inhibition.
        base_J2 (float): parameter representing amplitude of angle-specific
            interaction.
        dt (float): parameter representing the size of one timestep.
        J0 (float): parameter base_J0 normalized for the number of units.
        J2 (float): parameter base_J2 normalized for the number of units.
        N (int): integer number of units in the network. Thus unit i will
            represent neurons with preferred tuning at 2pi/i radians.
        K_inhib (float): Value of global inhibition
        J (numpy array): (N, N) array of floats representing the connectivity
            between units. V_ij will represent the connection from j to i.
        thetas (numpy array): (N,) array of float radians. The value at i
            represents the preferred tuning of unit i: 2pi/i
    """

    base_J0 = 0.3 
    base_J2 = 4.0
    dt = 0.1

    def __init__(self, N, K_inhib):
        self.N = N
        self.K_inhib = K_inhib
        self.J0 = self.base_J0/N
        self.J2 = self.base_J2/N
        self.thetas = np.linspace(0, 2*pi, N)
        self._init_J()

    def simulate(self, input_ext, alphas=None):
        """
        Simulates the behavior of the ring attractor over some period of time.
    
        Args:
            input_ext (numpy array): Size (T,) array of float radians representing
                the external stimulus. Here, the stimulus is some external cue
                that indicates what the correct orientation theta_0 is.
            alphas (numpy array): Size (T,) array of float representing the
                strength of the external input. Optional.

        Returns:
            m (numpy array): Size (N,T) array of floats representing current
                of each unit at each time step
            f (numpy array): Size (N,T) array of floats representing firing
                rate of each unit at each time step.

        Raises:
            ValueError: If alphas is provided but is not the same size as input.
        """
 
        if (alphas is not None) and (input_ext.size != alphas.size):
            raise ValueError(
                "If alphas is provided, it should be the same size as input."
                )
        T = input_ext.size
        m = np.zeros((self.N, T)) # Current
        f = np.zeros((self.N, T)) # Firing rate
        m0 = 0.1*np.random.normal(0, 1, self.N)
        for t in range(T):
            alpha_t = 0 if alphas is None else alphas[t]
            if t == 0:
                m_t, f_t = self._step(m0, input_ext[t], alpha_t)
            else:
                m_t, f_t = self._step(m[:, t-1], input_ext[t], alpha_t)
            m[:,t] = m_t
            f[:,t] = f_t
        return m, f

    def _step(self, prev_m, input_t, alpha_t):
        """
        Steps the network forward one time step. Evolves the current network
        activity according to the defined first-order dynamics.

        Args:
            prev_m (numpy array): (N,) size array of floats; the current
            input_t (float): Radian representing the external stimulus.
            alpha_t (float): The strength of the external stimulus

        Returns:
            m_{t} and f_{t}: numpy arrays representing the current and the
                firing rates, respectively, of each unit in the next time step.
        """

        h_ext = alpha_t*np.cos(input_t - self.thetas)
        f_t = self.J @ self._g(prev_m) + self._g(h_ext)
        dmdt = -prev_m + f_t - self.K_inhib
        m_t = prev_m + self.dt*dmdt 
        return m_t, f_t

    def _g(self, f_t):
        """
        Rectifies and saturates a given firing rate.
        """

        return np.clip(f_t, 0, 1)

    def _init_J(self):
        """
        Initializes the connectivity matrix J
        """

        J = np.zeros((self.N,self.N))
        for i in range(self.N):
            J[i,:]= -self.J0 + self.J2*np.cos(self.thetas[i] - self.thetas)
        self.J = J

class SimpleContextNetwork(RingNetwork):
    """
    A ring attractor network with context units external to the main network.
    A context unit synapses onto one ring unit.

    In this model, one timestep corresponds to 100 ms. 

    Args:
        N (int): Number of units in the network. Their preferred tuning evenly
           covers the ring
        N_c (int): Number of context units.
        C (float): parameter for the constant gain added to dmdt during the
            context mode.
        K_inhib (float): Value of global inhibition
        ring_indices (numpy array): Optional; size (N_c,) array containing the
            indices of the ring units that each context unit synapses onto. If
            not provided, they will be randomly drawn.

    Attributes:
        base_J0 (float): parameter representing uniform all-to-all inhibition.
        base_J2 (float): parameter representing amplitude of angle-specific
            interaction.
        dt (float): parameter representing the size of one timestep.
        J0 (float): parameter base_J0 normalized for the number of units.
        J2 (float): parameter base_J2 normalized for the number of units.
        N (int): integer number of units in the network. Thus unit i will
            represent neurons with preferred tuning at 2pi/i radians.
        N_c (int): Number of external context units.
        C (float): parameter for the constant gain added to dmdt during the
            context mode.
        K_inhib (float): Value of global inhibition
        ring_indices (numpy array): Optional; size (N_c,) array containing the
            indices of the ring unit that a context unit synapses onto. If not
            provided, they will be randomly drawn.
        J (numpy array): (N, N) array of floats representing the connectivity
            between units. V_ij will represent the connection from j to i.
        thetas (numpy array): (N,) array of float radians. The value at i
            represents the preferred tuning of unit i: 2pi/i
        ring_indices (numpy array): (N_c,) array containing the indices of the
            ring units that each context unit synapses onto.

    Raises:
        ValueError: If ring_indices.size != N_c
    """

    def __init__(self, N, N_c, C, K_inhib, ring_indices=None):
        self.N = N
        self.N_c = N_c
        self.C = C
        self.K_inhib = K_inhib
        self.J0 = self.base_J0/N
        self.J2 = self.base_J2/N
        self.thetas = np.linspace(0, 2*pi, N)
        if ring_indices is None:
            ring_indices = []
            for context in np.arange(N_c):
                ring_indices.append(np.random.choice(N, replace = False))
            self.ring_indices = np.array(ring_indices)
        else:
            if ring_indices.size != N_c:
                raise ValueError("Context unit indices are of incorrect size.")
            self.ring_indices = ring_indices
        self._init_J()

    def simulate(self, input_ext, input_c, alphas=None):
        """
        Simulates the behavior of the ring attractor over some period of time.
    
        Args:
            input_ext (numpy array): Size (T,) array of float radians representing
                the external stimulus. Here, the stimulus is some external cue
                that indicates what the correct orientation theta_0 is.
            input_c (numpy array): Size (T, N_c) array of floats representing
                the activation of context units over time.
            alphas (numpy array): Size (T,) array of float representing the
                strength of the external input. Optional.

        Returns:
            m (numpy array): Size (N,T) array of floats representing current
                of each unit at each time step
            f (numpy array): Size (N,T) array of floats representing firing
                rate of each unit at each time step.

        Raises:
            ValueError: If alphas is provided but is not the same size as input.
        """
 
        if (alphas is not None) and (input_ext.size != alphas.size):
            raise ValueError(
                "If alphas is provided, it should be the same size as input."
                )
        T = input_ext.size
        m = np.zeros((self.N, T)) # Current
        f = np.zeros((self.N, T)) # Firing rate
        dmdt = np.zeros((self.N, T))
        m0 = 0.1*np.random.normal(0, 1, self.N)
        for t in range(T):
            alpha_t = 0 if alphas is None else alphas[t]
            if t == 0:
                m_t, f_t, dmdt_t = self._step(
                    m0, input_ext[t], input_c[t], alpha_t
                    )
            else:
                m_t, f_t, dmdt_t = self._step(
                    m[:, t-1], input_ext[t], input_c[t], alpha_t
                    )
            m[:,t] = m_t
            f[:,t] = f_t
            dmdt[:,t] = dmdt_t
        return m, f, dmdt

    def _step(self, prev_m, input_ext_t, input_c_t, alpha_t):
        """
        Steps the network forward one time step. Evolves the current network
        activity according to the defined first-order dynamics.

        Args:
            prev_m (numpy array): (N,) size array of floats; the current
            input_t (float): Radian representing the external stimulus.
            input_c_t (numpy array): (N_c,) size array of floats; the activation
                of context units at this time step.
            alpha_t (float): The strength of the external stimulus

        Returns:
            m_{t} and f_{t}: numpy arrays representing the current and the
                firing rates, respectively, of each unit in the next time step.
        """

        h_ext = alpha_t*np.cos(input_ext_t - self.thetas)
        f_t = self.J @ self._g(prev_m) + self._g(h_ext)
        c_offset = np.zeros(self.N)
        c_offset[self.ring_indices] = input_c_t
        for i in range(1):
            c_offset[self.ring_indices + i + 1] = input_c_t
            c_offset[self.ring_indices - i - 1] = input_c_t
        c_offset *= self.C
        f_t += self._g(c_offset)
        dmdt = -prev_m + f_t - self.K_inhib
        m_t = prev_m + self.dt*dmdt
        return m_t, f_t, dmdt

class ContextNetwork(SimpleContextNetwork):
    """
    A ring attractor network with context units external to the main network.
    A context unit synapses onto multiple ring units. During a context mode,
    these ring units synapse onto a target unit with some strength.

    In this model, one timestep corresponds to 100 ms. 

    Args:
        N (int): Number of units in the network. Their preferred tuning evenly
           covers the ring
        N_c (int): Number of context units.
        C (float): parameter for the constant gain added to the dmdt for a
            ring unit when its connected context unit is activated.
        N_cr (int): Number of ring units that a single context unit synapses
            onto.
        J_cr (float): parameter; the synaptic strength from ring unit to target
            unit during context mode
        target_indices (numpy array): Optional; size (N_c,) array containing the
            indices of the target units. If not provided, they will be randomly
            drawn.

    Attributes:
        base_J0 (float): parameter representing uniform all-to-all inhibition.
        base_J2 (float): parameter representing amplitude of angle-specific
            interaction.
        dt (float): parameter representing the size of one timestep.
        J0 (float): parameter base_J0 normalized for the number of units.
        J2 (float): parameter base_J2 normalized for the number of units.
        N (int): integer number of units in the network. Thus unit i will
            represent neurons with preferred tuning at 2pi/i radians.
        N_c (int): Number of external context units.
        C (float): parameter for the constant gain added to dmdt during the
            context mode.
        N_cr (int): Number of ring units that a single context unit synapses
            onto.
        J_cr (float): parameter; the synaptic strength from ring unit to target
            unit during context mode
        J (numpy array): (N, N) array of floats representing the connectivity
            between units. V_ij will represent the connection from j to i.
        J_c (numpy array): (N, N) array of floats representing the connectivity
            between units during context mode. V_ij will represent the
            connection from j to i.
        thetas (numpy array): (N,) array of float radians. The value at i
            represents the preferred tuning of unit i: 2pi/i
        ring_indices (numpy array): (N_c, N_cr) array containing the indices of
            the ring units that the context units synapse onto.
        target_indices (numpy array): (N_c,) array containing the
            indices of the target units.

    Raises:
        ValueError: If target_indices.size != N_c
    """

    def __init__(self, N, N_c, C, K_inhib, N_cr, J_cr, target_indices=None):
        self.N = N
        self.N_c = N_c
        self.C = C
        self.K_inhib = K_inhib
        self.N_cr = N_cr
        self.J_cr = J_cr
        if target_indices is None:
            self.target_indices = np.random.choice(N, N_c, replace=False)
        else:
            if target_indices.size != N_c:
                raise ValueError("Target unit indices are of incorrect size.")
            self.target_indices = target_indices
        self._set_ring_cells()
        self.J0 = self.base_J0/N
        self.J2 = self.base_J2/N
        self.thetas = np.linspace(0, 2*pi, N)
        self._init_J()

    def _step(self, prev_m, input_t, input_c_t, alpha_t):
        """
        Steps the network forward one time step. Evolves the current network
        activity according to the defined first-order dynamics.

        Args:
            prev_m (numpy array): (N,) size array of floats; the current
            input_t (float): Radian representing the external stimulus.
            input_c_t (numpy array): (N_c,) size array of floats; the activation
                of context units at this time step.
            alpha_t (float): The strength of the external stimulus

        Returns:
            m_{t} and f_{t}: numpy arrays representing the current and the
                firing rates, respectively, of each unit in the next time step.
        """


        h_ext = alpha_t*np.cos(input_t - self.thetas)

        # Activate context to ring units first
        if np.sum(input_c_t) > 0:
            cr_input_c_t = np.tile(input_c_t, (self.N_cr,1)).T.flatten()
            cr_units = self.ring_indices.flatten()
            cr_f_t = self.J[cr_units,:] @ self._g(prev_m)
            cr_f_t += self._g(h_ext[cr_units])
            cr_dmdt = -prev_m[cr_units] + cr_f_t + self._g(cr_input_c_t*self.C)
            cr_dmdt -= self.K_inhib 
            cr_m_t = prev_m[cr_units] + self.dt*cr_dmdt
            prev_m[cr_units] = cr_m_t

        # Then, activate the rest of the units
        f_t = self.J @ self._g(prev_m) + self._g(h_ext)
        dmdt = -prev_m + f_t - self.K_inhib 
        m_t = prev_m + self.dt*dmdt
        return m_t, f_t, dmdt

    def _init_J(self):
        """
        Initializes the connectivity matrix J
        """

        J = np.zeros((self.N,self.N))
        for i in range(self.N):
            J[i,:]= -self.J0 + self.J2*np.cos(self.thetas[i] - self.thetas)
        for idx, cr_connections in enumerate(self.ring_indices):
            target_index = self.target_indices[idx]
            J[target_index, cr_connections] += self.J_cr
            for i in range(2):
                J[target_index + i + 1, cr_connections] += self.J_cr
                J[target_index - i - 1, cr_connections] += self.J_cr
        self.J = J

    def _set_ring_cells(self):
        """
        Determines what ring cells each context synapses onto
        """

        ring_indices = []
        for context in np.arange(self.N_c):
            ring_indices.append(np.random.choice(
                [i for i in range(self.N) if i not in self.target_indices],
                size=(self.N_cr,), replace=False
                ))
        self.ring_indices = np.array(ring_indices)

class MixedNetwork(ContextNetwork):
    """
    A ring attractor network with a single context-category unit external to the
    main network. This external unit synapses onto multiple ring units. These
    ring units themselves synapses onto many different target units. Each of
    these targets correspond to separate cache/memory sites; in other words, a
    single context from the activated context-category.

    In this model, one timestep corresponds to 100 ms. 

    Args:
        N (int): Number of units in the network. Their preferred tuning evenly
           covers the ring
        N_c (int): Number of contexts; they are represented by target units
        C (float): parameter for the constant gain added to the dmdt for a
            ring unit when its connected context unit is activated.
        N_cr (int): Number of ring units that the 
        J_cr (float): parameter; the synaptic strength from ring unit to target
            unit during context mode
        target_indices (numpy array): Optional; size (N_c,) array containing the
            indices of the target units. If not provided, they will be randomly
            drawn.

    Attributes:
        base_J0 (float): parameter representing uniform all-to-all inhibition.
        base_J2 (float): parameter representing amplitude of angle-specific
            interaction.
        dt (float): parameter representing the size of one timestep.
        J0 (float): parameter base_J0 normalized for the number of units.
        J2 (float): parameter base_J2 normalized for the number of units.
        N (int): integer number of units in the network. Thus unit i will
            represent neurons with preferred tuning at 2pi/i radians.
        N_c (int): Number of external context units.
        C (float): parameter for the constant gain added to dmdt during the
            context mode.
        N_cr (int): Number of ring units that a single context unit synapses
            onto.
        J_cr (float): parameter; the synaptic strength from ring unit to target
            unit during context mode
        J (numpy array): (N, N) array of floats representing the connectivity
            between units. V_ij will represent the connection from j to i.
        J_c (numpy array): (N, N) array of floats representing the connectivity
            between units during context mode. V_ij will represent the
            connection from j to i.
        thetas (numpy array): (N,) array of float radians. The value at i
            represents the preferred tuning of unit i: 2pi/i
        ring_indices (numpy array): (N_c, N_cr) array containing the indices of
            the ring units that the context units synapse onto.
        target_indices (numpy array): (N_c,) array containing the
            indices of the target units.

    Raises:
        ValueError: If target_indices.size != N_c
    """

    def __init__(self, N, N_c, C, K_inhib, N_cr, J_cr, target_indices=None):
        self.N = N
        self.N_c = N_c
        self.C = C
        self.K_inhib = K_inhib
        self.N_cr = N_cr
        self.J_cr = J_cr
        if target_indices is None:
            self.target_indices = np.random.choice(N, N_c, replace=False)
        else:
            if target_indices.size != N_c:
                raise ValueError("Target unit indices are of incorrect size.")
            self.target_indices = target_indices
        self.J0 = self.base_J0/N
        self.J2 = self.base_J2/N
        self.thetas = np.linspace(0, 2*pi, N)
        self._set_ring_cells()
        self._init_J()

    def _step(self, prev_m, input_t, input_c_t, alpha_t):
        """
        Steps the network forward one time step. Evolves the current network
        activity according to the defined first-order dynamics.

        Args:
            prev_m (numpy array): (N,) size array of floats; the current
            input_t (float): Radian representing the external stimulus.
            input_c_t (numpy array): (N_c,) size array of floats; the activation
                of context units at this time step.
            alpha_t (float): The strength of the external stimulus

        Returns:
            m_{t} and f_{t}: numpy arrays representing the current and the
                firing rates, respectively, of each unit in the next time step.
        """

        if type(input_c_t) is np.ndarray:
            raise ValueError("Context input array should be size (T,)")
        h_ext = alpha_t*np.cos(input_t - self.thetas)

        # Activate context to ring units first
        if input_c_t > 0:
            cr_units = np.unique(self.ring_indices.flatten())
            cr_input_c_t = np.ones(cr_units.size)*input_c_t
            cr_f_t = self.J[cr_units,:] @ self._g(prev_m)
            cr_f_t += self._g(h_ext[cr_units])
            cr_dmdt = -prev_m[cr_units] + cr_f_t + self._g(cr_input_c_t*self.C)
            cr_dmdt -= self.K_inhib 
            cr_m_t = prev_m[cr_units] + self.dt*cr_dmdt
            prev_m[cr_units] = cr_m_t

        # Then, activate the rest of the units
        f_t = self.J @ self._g(prev_m) + self._g(h_ext)
        dmdt = -prev_m + f_t - self.K_inhib 
        m_t = prev_m + self.dt*dmdt
        return m_t, f_t, dmdt

