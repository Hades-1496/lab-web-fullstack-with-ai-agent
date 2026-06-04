export const login = (email, password) => {
  if (password === 'demo-token-12345') {
    localStorage.setItem('token', password);
    return true;
  }
  return false;
};

export const logout = () => {
  localStorage.removeItem('token');
};

export const getToken = () => {
  return localStorage.getItem('token');
};