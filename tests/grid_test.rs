#[path="../src/lib.rs"]
mod ccbenchmark;
use ccbenchmark::grid::{Grid, unit::Unit, unit::TimeUnit, unit::MemoryUnit};

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn convert_unit_empty() {
        let grid = Grid::new(Unit::TimeUnit(TimeUnit::S), 0, 0);
        let new_unit_opt = grid.clone_convert_unit(&Unit::TimeUnit(TimeUnit::NS));

        if let Some(new_unit) = new_unit_opt {
            assert_eq!(new_unit.len(), 0)
        }
        else {
            panic!("invalid unit")
        }
    }
    #[test]
    fn convert_unit_one() {
        let mut grid = Grid::new(Unit::TimeUnit(TimeUnit::S), 1, 1);
        grid.set_column(0, &[1.0], Unit::TimeUnit(TimeUnit::S));
        let new_unit_opt = grid.clone_convert_unit(&Unit::TimeUnit(TimeUnit::NS));

        if let Some(new_unit) = new_unit_opt {
            assert_eq!(new_unit.column(0), &[1e9])
        }
        else {
            panic!("invalid unit")
        }
    }
    #[test]
    fn convert_unit() {
        let mut grid = Grid::new(Unit::TimeUnit(TimeUnit::S), 3, 3);
        grid.set_column(0, &[1.0, 2.0, 3.0], Unit::TimeUnit(TimeUnit::S));
        grid.set_column(1, &[4.0, 5.0, 6.0], Unit::TimeUnit(TimeUnit::S));
        grid.set_column(2, &[7.0, 8.0, 9.0], Unit::TimeUnit(TimeUnit::S));
        let new_unit_opt = grid.clone_convert_unit(&Unit::TimeUnit(TimeUnit::NS));

        if let Some(new_unit) = new_unit_opt {
            assert_eq!(new_unit.column(0), &[1e9, 2e9, 3e9]);
            assert_eq!(new_unit.column(1), &[4e9, 5e9, 6e9]);
            assert_eq!(new_unit.column(2), &[7e9, 8e9, 9e9]);
        }
        else {
            panic!("invalid unit")
        }
    }
    #[test]
    fn convert_unit_invalid_unit() {
        let mut grid = Grid::new(Unit::TimeUnit(TimeUnit::S), 3, 3);
        grid.set_column(0, &[1.0, 2.0, 3.0], Unit::TimeUnit(TimeUnit::S));
        grid.set_column(1, &[4.0, 5.0, 6.0], Unit::TimeUnit(TimeUnit::S));
        grid.set_column(2, &[7.0, 8.0, 9.0], Unit::TimeUnit(TimeUnit::S));
        let new_unit_opt = grid.clone_convert_unit(&Unit::MemoryUnit(MemoryUnit::KB));

        if let Some(_) = new_unit_opt {
            panic!("returned as Some instead of None")
        }
    }


    #[test]
    fn compare_neighbors_empty() {
        let col = Grid::new(Unit::TimeUnit(TimeUnit::S), 0, 0);
        let compare = col.clone_compare_neighbors(|base: f64, other: f64| base - other, Unit::TimeUnit(TimeUnit::S));

        assert_eq!(compare.len(), 0)
    }
    #[test]
    fn compare_neighbors_one() {
        let mut grid = Grid::new(Unit::TimeUnit(TimeUnit::S), 1, 1);
        grid.set_column(0, &[1.0], Unit::TimeUnit(TimeUnit::S));
        let compare = grid.clone_compare_neighbors(|base: f64, other: f64| base - other, Unit::TimeUnit(TimeUnit::S));

        assert!(compare.column(0)[0].is_nan());
    }
    #[test]
    fn compare_neighbors() {
        let mut grid = Grid::new(Unit::TimeUnit(TimeUnit::S), 3, 3);
        grid.set_column(0, &[1.0, 2.0, 3.0], Unit::TimeUnit(TimeUnit::S));
        grid.set_column(1, &[4.0, 5.0, 6.0], Unit::TimeUnit(TimeUnit::S));
        grid.set_column(2, &[7.0, 8.0, 9.0], Unit::TimeUnit(TimeUnit::S));
        let compare = grid.clone_compare_neighbors(|base: f64, other: f64| base - other, Unit::TimeUnit(TimeUnit::S));

        assert!(compare.column(0)[0].is_nan());
        assert!(compare.column(1)[0].is_nan());
        assert!(compare.column(2)[0].is_nan());

        assert_eq!(&compare.column(0)[1..], &[-1.0, -1.0]);
        assert_eq!(&compare.column(1)[1..], &[-1.0, -1.0]);
        assert_eq!(&compare.column(2)[1..], &[-1.0, -1.0]);
    }

    #[test]
    fn compare_index_empty() {
        let grid = Grid::new(Unit::TimeUnit(TimeUnit::S), 0, 0);
        let compare = grid.clone_compare_index(|base: f64, other: f64| base - other, Unit::TimeUnit(TimeUnit::S), 0);

        assert_eq!(compare.len(), 0)
    }

    #[test]
    fn compare_front_one() {
        let mut grid = Grid::new(Unit::TimeUnit(TimeUnit::S), 1, 1);
        grid.set_column(0, &[1.0], Unit::TimeUnit(TimeUnit::S));
        let compare = grid.clone_compare_index(|base: f64, other: f64| base - other, Unit::TimeUnit(TimeUnit::S), grid.front_col_index().unwrap());

        assert_eq!(compare.column(0), &[0.0]);
    }
    #[test]
    fn compare_front() {
        let mut grid = Grid::new(Unit::TimeUnit(TimeUnit::S), 3, 3);
        grid.set_column(0, &[1.0, 2.0, 3.0], Unit::TimeUnit(TimeUnit::S));
        grid.set_column(1, &[4.0, 5.0, 6.0], Unit::TimeUnit(TimeUnit::S));
        grid.set_column(2, &[7.0, 8.0, 9.0], Unit::TimeUnit(TimeUnit::S));
        let compare = grid.clone_compare_index(|base: f64, other: f64| base - other, Unit::TimeUnit(TimeUnit::S), grid.front_col_index().unwrap());

        assert_eq!(compare.column(0), &[0.0, -1.0, -2.0]);
        assert_eq!(compare.column(1), &[0.0, -1.0, -2.0]);
        assert_eq!(compare.column(2), &[0.0, -1.0, -2.0]);
    }

    #[test]
    fn compare_back_one() {
        let mut grid = Grid::new(Unit::TimeUnit(TimeUnit::S), 1, 1);
        grid.set_column(0, &[1.0], Unit::TimeUnit(TimeUnit::S));
        let compare = grid.clone_compare_index(|base: f64, other: f64| base - other, Unit::TimeUnit(TimeUnit::S), grid.back_col_index().unwrap());

        assert_eq!(compare.column(0), &[0.0]);
    }
    #[test]
    fn compare_back() {
        let mut grid = Grid::new(Unit::TimeUnit(TimeUnit::S), 3, 3);
        grid.set_column(0, &[1.0, 2.0, 3.0], Unit::TimeUnit(TimeUnit::S));
        grid.set_column(1, &[4.0, 5.0, 6.0], Unit::TimeUnit(TimeUnit::S));
        grid.set_column(2, &[7.0, 8.0, 9.0], Unit::TimeUnit(TimeUnit::S));
        let compare = grid.clone_compare_index(|base: f64, other: f64| base - other, Unit::TimeUnit(TimeUnit::S), grid.back_col_index().unwrap());

        assert_eq!(compare.column(0), &[2.0, 1.0, 0.0]);
        assert_eq!(compare.column(1), &[2.0, 1.0, 0.0]);
        assert_eq!(compare.column(2), &[2.0, 1.0, 0.0]);
    }
}