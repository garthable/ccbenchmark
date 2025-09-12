#[path="../src/lib.rs"]
mod ccbenchmark;
use ccbenchmark::{Unit, TimeUnit, MemoryUnit, PureUnit};

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn to_str_test() {
        let s = Unit::TimeUnit(TimeUnit::S);
        let b = Unit::MemoryUnit(MemoryUnit::B);
        let p = Unit::PureUnit(PureUnit::Percentage);

        assert_eq!(s.as_str(), "s");
        assert_eq!(b.as_str(), "b");
        assert_eq!(p.as_str(), "%");
    }
    #[test]
    fn to_scaler_test() {
        let s = Unit::TimeUnit(TimeUnit::S);
        let b = Unit::MemoryUnit(MemoryUnit::B);
        let p = Unit::PureUnit(PureUnit::Percentage);

        assert_eq!(s.as_scaler(), 1e9);
        assert_eq!(b.as_scaler(), 1.0);
        assert_eq!(p.as_scaler(), 1.0);
    }
}