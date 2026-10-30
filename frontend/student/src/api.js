export const API_URL = 'http://localhost:8000/api';

export const getStudentId = () => {
    const user = localStorage.getItem('student_user');
    if (user) {
        return JSON.parse(user).id;
    }
    return null;
};
