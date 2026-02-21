using System.Windows;
using LiveCharts;
using LiveCharts.Wpf;
using System.Windows.Threading;
using System;

namespace AttentionApp
{
    public partial class MainWindow : Window
    {
        private DispatcherTimer timer;
        private ChartValues<double> attentionValues;

        public MainWindow()
        {
            InitializeComponent();
            SetupDummyData();
            SetupTimer();
        }

        // Setup dummy graph and classroom
        private void SetupDummyData()
        {
            // Dummy attention values
            attentionValues = new ChartValues<double> { 0.8, 0.6, 0.9, 0.5, 0.7 };

            AttentionChart.Series = new SeriesCollection
            {
                new LineSeries
                {
                    Values = attentionValues,
                    Title = "Average Attention",
                    LineSmoothness = 0.5
                }
            };
        }

        // Setup timer to update graph and classroom map
        private void SetupTimer()
        {
            timer = new DispatcherTimer();
            timer.Interval = TimeSpan.FromSeconds(2);
            timer.Tick += Timer_Tick;
            timer.Start();
        }

        private void Timer_Tick(object sender, EventArgs e)
        {
            // Add new random attention value (0.5 - 1.0)
            var rnd = new Random();
            double newVal = 0.5 + rnd.NextDouble() * 0.5;
            attentionValues.Add(newVal);

            if (attentionValues.Count > 10)
                attentionValues.RemoveAt(0);

            // Update classroom map colors randomly
            foreach (var child in ClassroomMap.Children)
            {
                if (child is System.Windows.Shapes.Ellipse ellipse)
                {
                    double val = 0.5 + rnd.NextDouble() * 0.5;
                    if (val < 0.6) ellipse.Fill = System.Windows.Media.Brushes.Red;
                    else if (val < 0.8) ellipse.Fill = System.Windows.Media.Brushes.Yellow;
                    else ellipse.Fill = System.Windows.Media.Brushes.Green;
                }
            }
        }
    }
}
