import dynamic from 'next/dynamic';

const TestChart = dynamic(() => import('@/components/TestChart'), {
  ssr: false,
  loading: () => (
    <div className="w-full h-[400px] bg-dark-card flex items-center justify-center">
      <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )
});

const TestChartPage = () => {
  return (
    <div className="min-h-screen bg-dark-bg p-8">
      <h1 className="text-2xl font-bold text-white mb-8">K线图测试</h1>
      <div className="bg-dark-card border border-dark-border rounded-xl p-4">
        <TestChart />
      </div>
    </div>
  );
};

export default TestChartPage;
