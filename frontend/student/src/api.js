const isLocalDev = window.location.hostname === 'localhost' && window.location.port !== '8000' && window.location.port !== '';
export const API_URL = isLocalDev ? 'http://localhost:8000/api' : '/api';

export const getStudentId = () => {
    const user = localStorage.getItem('student_user');
    if (user) {
        return JSON.parse(user).id;
    }
    return null;
};
