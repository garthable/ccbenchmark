#[path="../src/lib.rs"]
mod ccbenchmark;
use ccbenchmark::manager::{Manager, Profile, unit::{Unit, TimeUnit}, grid::Grid};

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn run_profile_single_test() {
        let mut manager = Manager::new();

        let mut grid = Grid::new(Unit::TimeUnit(TimeUnit::S), 3, 3);
        grid.set_column(0, &[1.0, 2.0, 3.0], Unit::TimeUnit(TimeUnit::S));
        grid.set_column(1, &[4.0, 5.0, 6.0], Unit::TimeUnit(TimeUnit::S));
        grid.set_column(2, &[7.0, 8.0, 9.0], Unit::TimeUnit(TimeUnit::S));
        manager.push(grid);

        let profile = Profile { 
            selected_indicies: vec![0], 
            unit: "s".to_string()
        };
        let output = manager.run_profile(&profile);

        assert_eq!(output[0], &["1.00 s", "2.00 s", "3.00 s"]);
        assert_eq!(output[2], &["4.00 s", "5.00 s", "6.00 s"]);
        assert_eq!(output[4], &["7.00 s", "8.00 s", "9.00 s"]);

        assert_eq!(output[1], &["NaN %", "100.00 %", "50.00 %"]);
        assert_eq!(output[3], &["NaN %", "25.00 %", "20.00 %"]);
        assert_eq!(output[5], &["NaN %", "14.29 %", "12.50 %"]);
    }

    #[test]
    fn run_profile_multi_test() {
        let mut manager = Manager::new();

        let mut grid: Grid = Grid::new(Unit::from_str("s"), 3, 3);
        grid.set_column(0, &[1.0, 2.0, 3.0], Unit::TimeUnit(TimeUnit::S));
        grid.set_column(1, &[4.0, 5.0, 6.0], Unit::TimeUnit(TimeUnit::S));
        grid.set_column(2, &[7.0, 8.0, 9.0], Unit::TimeUnit(TimeUnit::S));
        manager.push(grid.clone());
        grid = Grid::new(Unit::from_str("s"), 3, 3);
        grid.set_column(0, &[1.5, 2.5, 3.5], Unit::TimeUnit(TimeUnit::S));
        grid.set_column(1, &[4.5, 5.5, 6.5], Unit::TimeUnit(TimeUnit::S));
        grid.set_column(2, &[7.5, 8.5, 9.5], Unit::TimeUnit(TimeUnit::S));
        manager.push(grid.clone());
        grid = Grid::new(Unit::from_str("s"), 3, 3);
        grid.set_column(0, &[1.2, 2.2, 3.2], Unit::TimeUnit(TimeUnit::S));
        grid.set_column(1, &[4.2, 5.2, 6.2], Unit::TimeUnit(TimeUnit::S));
        grid.set_column(2, &[7.2, 8.2, 9.2], Unit::TimeUnit(TimeUnit::S));
        manager.push(grid.clone());

        let profile = Profile { 
            selected_indicies: vec![0, 1, 2], 
            unit: "s".to_string()
        };
        let output = manager.run_profile(&profile);

        assert_eq!(output[0], &["3.00 s", "3.50 s", "3.20 s"]);
        assert_eq!(output[2], &["6.00 s", "6.50 s", "6.20 s"]);
        assert_eq!(output[4], &["9.00 s", "9.50 s", "9.20 s"]);

        assert_eq!(output[1], &["0.00 %", "16.67 %", "6.67 %"]);
        assert_eq!(output[3], &["0.00 %", "8.33 %", "3.33 %"]);
        assert_eq!(output[5], &["0.00 %", "5.56 %", "2.22 %"]);
    }
}