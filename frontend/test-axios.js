// 在浏览器中测试 axios 请求
const testAxios = async () => {
  console.log('testAxios called');
  try {
    const response = await fetch('/api/stocks/600071/summary');
    const data = await response.json();
    console.log('Fetch response:', data);
    return data;
  } catch (error) {
    console.error('Fetch error:', error);
    throw error;
  }
};

// 导出供测试
if (typeof module !== 'undefined') {
  module.exports = testAxios;
}
