import * as yup from 'yup'

// Schema לולידציה
const signupSchema = yup.object({
  username: yup.string().min(2, 'שם המשתמש חייב להיות לפחות 2 תווים').required('שדה חובה'),
  email: yup.string().email('כתובת אימייל לא תקינה').required('שדה חובה'),
  password: yup.string().min(8, 'Ensure this field has at least 8 characters').required('שדה חובה'),
  password_confirm: yup
    .string()
    .oneOf([yup.ref('password')], 'הסיסמאות אינן תואמות')
    .required('שדה חובה'),
})

const signinSchema = yup.object({
  username: yup
    .string()
    .required('שדה חובה')
    .test('valid-username-or-email', 'Username must contain only English letters and numbers', function(value) {
      if (!value) return false;
      // אם נראה כמו email (יש @), מאפשרים אותו
      if (value.includes('@')) return true;
      // אחרת בודקים שזה username חוקי - רק אותיות באנגלית ומספרים
      return /^[a-zA-Z0-9]+$/.test(value);
    }),
  password: yup.string().required('שדה חובה'),
})

const forgotPasswordSchema = yup.object({
  email: yup.string().email('כתובת אימייל לא תקינה').required('שדה חובה'),
})

const resetPasswordSchema = yup.object({
  password: yup.string().min(8, 'Ensure this field has at least 8 characters').required('שדה חובה'),
  password_confirm: yup
    .string()
    .oneOf([yup.ref('password')], 'הסיסמאות אינן תואמות')
    .required('שדה חובה'),
  uid: yup.string().required('שדה חובה'),
  token: yup.string().required('שדה חובה'),
})

const verifyEmailSchema = yup.object({
  key: yup.string().required('שדה חובה'),
})

export { 
  signupSchema, 
  signinSchema, 
  forgotPasswordSchema, 
  resetPasswordSchema,
  verifyEmailSchema 
}