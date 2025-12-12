import toast from 'react-hot-toast';

export const notify = {
  success: (message: string) => {
    toast.success(message, {
      icon: '✅',
    });
  },
  error: (message: string) => {
    toast.error(message, {
      icon: '❌',
    });
  },
  warning: (message: string) => {
    toast(message, {
      icon: '⚠️',
      style: {
        background: '#ffc107',
        color: '#212529',
      },
    });
  },
  info: (message: string) => {
    toast(message, {
      icon: 'ℹ️',
      style: {
        background: '#17a2b8',
        color: '#fff',
      },
    });
  },
  loading: (message: string) => {
    return toast.loading(message);
  },
  dismiss: (toastId: string) => {
    toast.dismiss(toastId);
  },
};

